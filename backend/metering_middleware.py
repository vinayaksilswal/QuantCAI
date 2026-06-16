import time
import json
import hashlib
import logging
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models as DBmodels
from core.database import get_db
from security import redis_client

logger = logging.getLogger("quantcai.metering")

# ---------------------------------------------------------------------------
# Unified Atomic Gate — Token Bucket + Wallet Check (Security: Finding #3)
# ---------------------------------------------------------------------------
# This Lua script atomically performs ALL checks in a single Redis round-trip:
#   1. Checks wallet_blocked flag
#   2. Enforces token-bucket rate limiting
# Eliminates the TOCTOU race condition where concurrent requests could all
# pass the blocked check before any of them set the flag.
LUA_ATOMIC_GATE = """
local rate_key = KEYS[1]
local blocked_key = KEYS[2]

local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

-- 1. Check if wallet is already blocked (atomic read)
local blocked = redis.call('get', blocked_key)
if blocked == '1' then
    return {0, 'WALLET_BLOCKED'}
end

-- 2. Token bucket rate limiting (atomic)
local tokens = capacity
local exists = redis.call('exists', rate_key)
if exists == 1 then
    local last_tokens = tonumber(redis.call('hget', rate_key, 'tokens'))
    local last_time = tonumber(redis.call('hget', rate_key, 'last_updated'))
    local elapsed = math.max(0, now - last_time)
    tokens = math.min(capacity, last_tokens + elapsed * refill_rate)
end

if tokens < 1 then
    return {0, 'RATE_LIMITED'}
end

tokens = tokens - 1
redis.call('hset', rate_key, 'tokens', tokens, 'last_updated', now)
redis.call('expire', rate_key, 60)

return {1, 'OK'}
"""

def hash_key_sha256(key: str) -> str:
    """Hash an API key using SHA-256 for database lookup."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

async def get_or_create_wallet(db: AsyncSession, user_id: int) -> DBmodels.WalletBalance:
    """Helper to get a user's wallet balance or create one with zero credits if missing."""
    stmt = select(DBmodels.WalletBalance).where(DBmodels.WalletBalance.user_id == user_id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()
    if not wallet:
        wallet = DBmodels.WalletBalance(user_id=user_id, balance_credits=0.0)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
    return wallet

async def verify_api_key_and_meter(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    FastAPI dependency that validates the X-API-Key, enforces the token bucket rate limit,
    and checks if the wallet balance is positive.
    """
    api_key_val = request.headers.get("X-API-Key")
    if not api_key_val:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is missing"
        )

    # 1. Hash key for verification
    hashed_key = hash_key_sha256(api_key_val)
    cache_key = f"developer:apikey:{hashed_key}"

    # 2. Check key status cache
    cached_info = await redis_client.get(cache_key)
    if cached_info:
        key_info = json.loads(cached_info)
    else:
        # Fallback to DB
        stmt = select(DBmodels.ApiKey).where(DBmodels.ApiKey.hashed_key == hashed_key)
        res = await db.execute(stmt)
        api_key = res.scalar_one_or_none()

        if not api_key or not api_key.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive API Key"
            )

        wallet = await get_or_create_wallet(db, api_key.user_id)

        key_info = {
            "id": api_key.id,
            "user_id": api_key.user_id,
            "prefix": api_key.prefix,
            "name": api_key.name,
            "is_active": api_key.is_active,
        }
        # Cache for 10 minutes (600 seconds)
        # Cache for 60 seconds (reduced from 600s to limit stale-key window — Finding #3)
        await redis_client.setex(cache_key, 60, json.dumps(key_info))
        # Cache wallet balance as well if not already cached
        wallet_cache_key = f"developer:wallet:{api_key.user_id}"
        await redis_client.set(wallet_cache_key, str(wallet.balance_credits))

    user_id = key_info["user_id"]
    api_key_id = key_info["id"]

    # --- ENFORCE DAILY TIER LIMITS ---
    from tier_limits import get_user_tier
    tier = await get_user_tier(db, user_id)
    daily_api_limit = 10 if tier == "FREE" else 500 if tier == "PRO" else 9999999
    
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    usage_key = f"developer:usage:daily:{api_key_id}:{today_str}"
    
    daily_requests = await redis_client.hget(usage_key, "requests")
    if daily_requests and int(daily_requests) >= daily_api_limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Daily Developer API limit of {daily_api_limit} requests reached for your tier."
        )

    # 3+4. Atomic wallet check + token bucket rate limit (Finding #3)
    # Both checks run in a single Redis round-trip via Lua, eliminating TOCTOU.
    rate_key = f"developer:rate_limit:{api_key_id}"
    blocked_key = f"developer:wallet_blocked:{user_id}"
    gate_result = await redis_client.eval(
        LUA_ATOMIC_GATE, 2, rate_key, blocked_key,
        60, 1.0, time.time()
    )

    if gate_result[0] == 0:
        reason = gate_result[1] if len(gate_result) > 1 else "UNKNOWN"
        if reason == "WALLET_BLOCKED":
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient funds. Your wallet balance is empty or below the safety threshold."
            )
        elif reason == "RATE_LIMITED":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Standard limit is 60 requests/minute."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Request denied by atomic gate check."
            )

    # Save to state for route usage
    request.state.api_key_id = api_key_id
    request.state.user_id = user_id
    request.state.hashed_key = hashed_key
    request.state.tier = tier

    return key_info

async def apply_transaction_charges(user_id: int, api_key_id: int, shots: int):
    """
    Deducts a micro-charge from the cached wallet balance and updates the daily usage hash.
    Standard rate: $0.00015 (0.015 cents) per 1024 shots.
    """
    # Calculate charge: e.g., 0.015 cents per 1024 shots
    # Charge per shot = 0.015 / 1024
    charge_cents = float((shots / 1024.0) * 0.015)

    wallet_cache_key = f"developer:wallet:{user_id}"
    
    # Atomic decrement of the cached balance
    try:
        # We use decrbyfloat / incrbyfloat with negative number to deduct balance
        new_balance = await redis_client.incrbyfloat(wallet_cache_key, -charge_cents)
        await redis_client.incrbyfloat(f"developer:wallet_pending:{user_id}", charge_cents)
    except Exception as e:
        logger.error(f"Failed to deduct balance in Redis: {e}")
        return

    # Check safety threshold (<= 0)
    if new_balance <= 0:
        await redis_client.set(f"developer:wallet_blocked:{user_id}", "1")

    # Increment daily usage metrics
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    usage_key = f"developer:usage:daily:{api_key_id}:{today_str}"
    
    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.hincrby(usage_key, "requests", 1)
        pipe.hincrby(usage_key, "total_shots", shots)
        pipe.hincrbyfloat(usage_key, "total_spend", charge_cents)
        pipe.expire(usage_key, 86400 * 35) # keep daily hashes for 35 days in Redis
        await pipe.execute()

    logger.info(f"Transaction successful. Charged user {user_id} {charge_cents:.6f} credits. New balance: {new_balance:.6f}")


async def flush_cumulative_metrics_to_db():
    """
    Flushes cumulative daily usage and wallet balances from Redis to PostgreSQL.
    Intended to be run periodically (e.g., every 5 minutes).
    """
    logger.info("Starting periodic sync of Redis metrics to PostgreSQL...")
    from core.database import async_session_factory
    from models_billing import DailyUsageRollup
    
    # 1. Sync wallet balances
    wallet_keys = []
    cursor = 0
    while True:
        cursor, keys = await redis_client.scan(cursor, match="developer:wallet_pending:*")
        wallet_keys.extend(keys)
        if cursor == 0:
            break
            
    async with async_session_factory() as session:
        from sqlalchemy import update
        for w_key in wallet_keys:
            try:
                user_id_str = w_key.split(":")[-1]
                if not user_id_str.isdigit():
                    continue
                
                # Fetch pending debits and clear the key atomically
                debited_amount = await redis_client.getdel(w_key)
                if not debited_amount or float(debited_amount) <= 0:
                    continue
                    
                # SECURITY FIX (Finding #5): Use atomic increment/decrement query
                stmt = update(DBmodels.WalletBalance).where(
                    DBmodels.WalletBalance.user_id == int(user_id_str)
                ).values(
                    balance_credits=DBmodels.WalletBalance.balance_credits - float(debited_amount)
                )
                await session.execute(stmt)
                logger.debug(f"Atomically synced wallet for user {user_id_str}, debited: {debited_amount}")
            except Exception as e:
                logger.error(f"Error processing wallet key {w_key}: {e}")
                
        # 2. Sync daily usage rollups
        usage_keys = []
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor, match="developer:usage:daily:*")
            usage_keys.extend(keys)
            if cursor == 0:
                break
                
        for u_key in usage_keys:
            try:
                # Format: developer:usage:daily:{api_key_id}:{date_str}
                parts = u_key.split(":")
                api_key_id = int(parts[3])
                date_str = parts[4]
                
                usage_data = await redis_client.hgetall(u_key)
                if usage_data:
                    requests = int(usage_data.get("requests", 0))
                    shots = int(usage_data.get("total_shots", 0))
                    spend = float(usage_data.get("total_spend", 0.0))
                    
                    stmt = select(DailyUsageRollup).where(
                        DailyUsageRollup.api_key_id == api_key_id,
                        DailyUsageRollup.usage_date == date_str
                    )
                    res = await session.execute(stmt)
                    rollup = res.scalar_one_or_none()
                    
                    if rollup:
                        rollup.requests_count = requests
                        rollup.total_shots = shots
                        rollup.total_spend = spend
                        session.add(rollup)
                    else:
                        rollup = DailyUsageRollup(
                            api_key_id=api_key_id,
                            usage_date=date_str,
                            requests_count=requests,
                            total_shots=shots,
                            total_spend=spend
                        )
                        session.add(rollup)
            except Exception as e:
                logger.error(f"Error syncing daily usage rollup for key {u_key}: {e}")
                
        await session.commit()
    logger.info("Periodic sync of Redis metrics to PostgreSQL completed successfully.")
