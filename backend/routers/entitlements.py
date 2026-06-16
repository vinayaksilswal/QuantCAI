from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

import models as DBmodels
from core.database import get_db
from security import get_current_user, redis_client
from tier_limits import get_user_tier

router = APIRouter(prefix="/api/v1/entitlements", tags=["Entitlements & Plan Matrix"])

@router.get("")
async def get_user_entitlements(
    db: AsyncSession = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user)
):
    """
    Returns the entitlement matrix, limits, and current usage indicators 
    for the authenticated user based on their subscription tier.
    """
    tier = await get_user_tier(db, current_user.id)

    # Retrieve cycle reset date from UserPlan
    stmt_plan = select(DBmodels.UserPlan).where(DBmodels.UserPlan.user_id == current_user.id)
    res_plan = await db.execute(stmt_plan)
    user_plan = res_plan.scalar_one_or_none()
    cycle_reset_date = user_plan.cycle_reset_date.strftime("%Y-%m-%d") if user_plan else date.today().strftime("%Y-%m-%d")

    # Retrieve usage from FeatureUsage table
    stmt_usage = select(DBmodels.FeatureUsage).where(DBmodels.FeatureUsage.user_id == current_user.id)
    res_usage = await db.execute(stmt_usage)
    usage = res_usage.scalar_one_or_none()

    # Retrieve AI chats count from Redis (ensures instant consistency)
    redis_key = f"user:{current_user.id}:ai_chats:count"
    chats_count_val = await redis_client.get(redis_key)
    chats_count = int(chats_count_val) if chats_count_val is not None else 0

    pqc_scans = usage.monthly_pqc_scans if usage else 0
    compute_overhead = usage.total_compute_overhead if usage else 0.0

    # Limits mapping matrix
    limits_matrix = {
        "FREE": {
            "qubits": 3,
            "depth": 15,
            "shots": 1024,
            "noise_models": ["ideal"],
            "ai_chats_daily": 10,
            "pqc_scans_monthly": 3,
            "api_requests_daily": 10,
            "circuit_runs_daily": 10,
            "custom_cbom": False,
            "internal_scanning": False,
            "qpu_priority": False
        },
        "PRO": {
            "qubits": 15,
            "depth": -1,  # -1 represents unlimited/unconstrained
            "shots": 65536,
            "noise_models": ["ideal", "depolarizing", "thermal"],
            "ai_chats_daily": -1,
            "pqc_scans_monthly": 50,
            "api_requests_daily": 500,
            "circuit_runs_daily": 500,
            "custom_cbom": False,
            "internal_scanning": False,
            "qpu_priority": False
        },
        "ENTERPRISE": {
            "qubits": -1,
            "depth": -1,
            "shots": -1,
            "noise_models": ["ideal", "depolarizing", "thermal"],
            "ai_chats_daily": -1,
            "pqc_scans_monthly": -1,
            "api_requests_daily": -1,
            "circuit_runs_daily": -1,
            "custom_cbom": True,
            "internal_scanning": True,
            "qpu_priority": True
        }
    }

    tier_limits = limits_matrix.get(tier, limits_matrix["FREE"])

    return {
        "tier": tier,
        "cycle_reset_date": cycle_reset_date,
        "usage": {
            "daily_ai_chats": chats_count,
            "monthly_pqc_scans": pqc_scans,
            "total_compute_overhead": compute_overhead
        },
        "limits": tier_limits
    }
