import ipaddress
import socket
import logging
from datetime import datetime, date, timedelta, time, timezone
from typing import Any, Dict, Optional, List
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models as DBmodels
from core.database import get_db
from security import redis_client, get_current_user_or_api_key

logger = logging.getLogger("quantcai.limits")

LUA_AI_CHAT_LIMITER = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local ttl = tonumber(ARGV[2])

local count = tonumber(redis.call('get', key) or '0')
if count >= limit then
    return -1  -- limit exceeded
end

if count == 0 then
    redis.call('setex', key, ttl, 1)
else
    redis.call('incr', key)
end

return count + 1
"""

def is_internal_domain(domain: str) -> bool:
    """
    Checks if a domain resolves to a private IP, loopback, or internal hostname.
    """
    domain_clean = domain.strip().lower()
    if domain_clean.startswith("https://"):
        domain_clean = domain_clean[8:]
    elif domain_clean.startswith("http://"):
        domain_clean = domain_clean[7:]
    if "/" in domain_clean:
        domain_clean = domain_clean.split("/")[0]
    if ":" in domain_clean:
        domain_clean = domain_clean.split(":")[0]

    if domain_clean in ("localhost", "127.0.0.1", "::1") or domain_clean.endswith(".local") or domain_clean.endswith(".lan"):
        return True

    try:
        ip = ipaddress.ip_address(domain_clean)
        return ip.is_private or ip.is_loopback
    except ValueError:
        try:
            # Try resolving DNS
            ip_str = socket.gethostbyname(domain_clean)
            ip = ipaddress.ip_address(ip_str)
            return ip.is_private or ip.is_loopback
        except Exception:
            pass
    return False

def calculate_gates_depth(gates: list, num_qubits: int) -> int:
    """
    Calculate circuit depth from list of gates.
    """
    depths = {i: 0 for i in range(num_qubits)}
    for gate in gates:
        qubits = gate.get("qubits", []) if isinstance(gate, dict) else getattr(gate, "qubits", [])
        if not qubits:
            continue
        max_q_depth = max(depths.get(q, 0) for q in qubits)
        new_depth = max_q_depth + 1
        for q in qubits:
            depths[q] = new_depth
    return max(depths.values()) if depths else 0

def _extract_qubit_count(qasm_str: str) -> int:
    import re
    total = 0
    for match in re.finditer(r"qreg\s+\w+\s*\[\s*(\d+)\s*\]", qasm_str):
        total += int(match.group(1))
    # OpenQASM 3.0 qubit declaration format: qubit[5] q;
    for match in re.finditer(r"qubit\s*\[\s*(\d+)\s*\]", qasm_str):
        total += int(match.group(1))
    return total

async def get_user_tier(db: AsyncSession, user_id: int) -> str:
    """
    Fetch the tier of the user. Automatically migrates/initializes UserPlan 
    and FeatureUsage if they don't exist.
    """
    stmt = select(DBmodels.UserPlan).where(DBmodels.UserPlan.user_id == user_id)
    res = await db.execute(stmt)
    plan = res.scalar_one_or_none()

    if plan:
        # Check if cycle date needs to be reset (monthly reset)
        if plan.cycle_reset_date <= date.today():
            usage_stmt = select(DBmodels.FeatureUsage).where(DBmodels.FeatureUsage.user_id == user_id)
            usage_res = await db.execute(usage_stmt)
            usage = usage_res.scalar_one_or_none()
            if usage:
                usage.monthly_pqc_scans = 0
                db.add(usage)
            plan.cycle_reset_date = date.today() + timedelta(days=30)
            db.add(plan)
            await db.commit()
            await db.refresh(plan)
        return plan.tier.value

    # Fallback to legacy subscriptions
    from security import get_subscription_plan
    user_stmt = select(DBmodels.User).where(DBmodels.User.id == user_id)
    res_user = await db.execute(user_stmt)
    user = res_user.scalar_one_or_none()
    org_id = user.org_id if user else None

    tier_str = await get_subscription_plan(db, user_id, org_id)
    tier_enum = DBmodels.Tier.FREE
    if tier_str.lower() == "pro":
        tier_enum = DBmodels.Tier.PRO
    elif tier_str.lower() == "enterprise":
        tier_enum = DBmodels.Tier.ENTERPRISE

    # Initialize UserPlan
    plan = DBmodels.UserPlan(
        user_id=user_id,
        tier=tier_enum,
        cycle_reset_date=date.today() + timedelta(days=30)
    )
    db.add(plan)

    # Initialize FeatureUsage
    usage = DBmodels.FeatureUsage(
        user_id=user_id,
        daily_ai_chats=0,
        monthly_pqc_scans=0,
        total_compute_overhead=0.0
    )
    db.add(usage)
    await db.commit()

    return tier_enum.value

def enforce_limits(required_feature: str):
    """
    Global dependency constructor to enforce subscription tier limits.
    """
    async def dependency(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user: DBmodels.User = Depends(get_current_user_or_api_key)
    ):
        tier = await get_user_tier(db, current_user.id)
        request.state.tier = tier

        if required_feature == "circuit" or required_feature == "simulator":
            # Verify body fields
            try:
                body = await request.json()
            except Exception:
                body = {}

            num_qubits = body.get("num_qubits")
            shots = body.get("shots")
            
            # extract noise parameters
            use_noise = body.get("use_noise")
            noise_model = body.get("noise_model")
            has_noise = use_noise or (noise_model and str(noise_model).lower() not in ("ideal", "none", "false"))

            gates = body.get("gates", [])
            qasm_string = body.get("qasm_string") or body.get("circuit_qasm")

            # Parse QASM if present to determine qubit count and depth
            depth = 0
            if qasm_string:
                try:
                    from qiskit import QuantumCircuit
                    import qiskit.qasm3 as q3
                    if "OPENQASM 3.0" in qasm_string or "OPENQASM 3" in qasm_string:
                        qc = q3.loads(qasm_string)
                    else:
                        qc = QuantumCircuit.from_qasm_str(qasm_string)
                    num_qubits = qc.num_qubits
                    depth = qc.depth()
                except Exception:
                    # Fallback to regex & estimation
                    num_qubits = num_qubits or _extract_qubit_count(qasm_string)
            else:
                depth = calculate_gates_depth(gates, num_qubits or 5)

            # Limit checking
            if tier == "FREE":
                if num_qubits and num_qubits > 3:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail={"error": "QUBIT_LIMIT_EXCEEDED", "message": "Free tier is limited to 3 qubits. Upgrade to Pro for up to 15 qubits."}
                    )
                if depth and depth > 15:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail={"error": "DEPTH_LIMIT_EXCEEDED", "message": "Free tier is limited to circuit depth of 15. Upgrade to Pro for unlimited depth."}
                    )
                if shots and shots > 1024:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail={"error": "SHOTS_LIMIT_EXCEEDED", "message": "Free tier is limited to 1,024 shots. Upgrade to Pro for up to 65,536 shots."}
                    )
                if has_noise:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail={"error": "NOISE_MODEL_RESTRICTED", "message": "Noise models are restricted on the Free tier. Upgrade to Pro for Thermal/Depolarizing noise."}
                    )
            elif tier == "PRO":
                if num_qubits and num_qubits > 15:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail={"error": "QUBIT_LIMIT_EXCEEDED", "message": "Pro tier is limited to 15 qubits. Upgrade to Enterprise for unlimited execution."}
                    )
                if shots and shots > 65536:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail={"error": "SHOTS_LIMIT_EXCEEDED", "message": "Pro tier is limited to 65,536 shots. Upgrade to Enterprise for unlimited execution."}
                    )
            # Enterprise has no limitations

            # Redis rate limiting for daily circuit runs
            redis_key = f"user:{current_user.id}:circuit_runs:count"
            now = datetime.now(timezone.utc)
            tomorrow = datetime.combine(now.date() + timedelta(days=1), time.min, tzinfo=timezone.utc)
            seconds_until_midnight = int((tomorrow - now).total_seconds())

            run_limit = 10 if tier == "FREE" else 500 if tier == "PRO" else 999999
            
            result = await redis_client.eval(
                LUA_AI_CHAT_LIMITER, 1, redis_key, 
                run_limit,  
                seconds_until_midnight
            )
            
            if result == -1:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "error": "RUN_LIMIT_EXCEEDED", 
                        "reset_in_seconds": seconds_until_midnight, 
                        "message": f"Daily simulator limit of {run_limit} runs reached. Upgrade your tier for more runs."
                    }
                )

        elif required_feature == "pqc":
            # Extract domain
            domain = request.path_params.get("domain")
            if not domain:
                try:
                    body = await request.json()
                    domain = body.get("domain")
                except Exception:
                    pass

            if domain:
                if is_internal_domain(domain) and tier != "ENTERPRISE":
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail={"error": "ENTERPRISE_REQUIRED", "message": "Internal subnet scanning requires an Enterprise tier subscription."}
                    )

            # Check monthly audit limits (Security: Finding #10 TOCTOU Fix)
            usage_stmt = (
                select(DBmodels.FeatureUsage)
                .where(DBmodels.FeatureUsage.user_id == current_user.id)
                .with_for_update()  # Lock the row
            )
            usage_res = await db.execute(usage_stmt)
            usage = usage_res.scalar_one_or_none()

            if not usage:
                usage = DBmodels.FeatureUsage(
                    user_id=current_user.id,
                    daily_ai_chats=0,
                    monthly_pqc_scans=0,
                    total_compute_overhead=0.0
                )
                db.add(usage)
                await db.flush()  # Flush to get the lock

            if tier == "FREE" and usage.monthly_pqc_scans >= 3:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={"error": "PQC_LIMIT_EXCEEDED", "message": "Free tier limit of 3 PQC scans per month reached. Upgrade to Pro for up to 50 scans."}
                )
            elif tier == "PRO" and usage.monthly_pqc_scans >= 50:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={"error": "PQC_LIMIT_EXCEEDED", "message": "Pro tier limit of 50 PQC scans per month reached. Upgrade to Enterprise for unlimited scans."}
                )

            # Increment count atomically (protected by row lock)
            usage.monthly_pqc_scans += 1
            db.add(usage)
            await db.commit()

        elif required_feature == "quantai":
            # Redis rate limiting for daily messages (Security: Finding #11 TOCTOU Fix)
            redis_key = f"user:{current_user.id}:ai_chats:count"

            # Calculate seconds to midnight for Redis TTL
            now = datetime.now(timezone.utc)
            tomorrow = datetime.combine(now.date() + timedelta(days=1), time.min, tzinfo=timezone.utc)
            seconds_until_midnight = int((tomorrow - now).total_seconds())

            # Check and increment atomically via Lua
            limit = 10 if tier == "FREE" else 999999
            result = await redis_client.eval(
                LUA_AI_CHAT_LIMITER, 1, redis_key, 
                limit,  
                seconds_until_midnight
            )
            
            if result == -1:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "AI_LIMIT_EXCEEDED", 
                        "reset_in_seconds": seconds_until_midnight, 
                        "message": "Daily AI chat limit of 10 messages reached. Upgrade to Pro for unlimited chats."
                    }
                )

            # Sync with database
            usage_stmt = select(DBmodels.FeatureUsage).where(DBmodels.FeatureUsage.user_id == current_user.id)
            usage_res = await db.execute(usage_stmt)
            usage = usage_res.scalar_one_or_none()

            if not usage:
                usage = DBmodels.FeatureUsage(
                    user_id=current_user.id,
                    daily_ai_chats=0,
                    monthly_pqc_scans=0,
                    total_compute_overhead=0.0
                )
                db.add(usage)
            
            usage.daily_ai_chats += 1
            db.add(usage)
            await db.commit()

    return dependency
