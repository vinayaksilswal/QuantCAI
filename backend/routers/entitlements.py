from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

import models as DBmodels
from core.database import get_db
from core.config import settings
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
    tier = tier.upper() if tier else "FREE"

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

    # Retrieve centralized limits from settings
    tier_limits = settings.TIER_LIMITS.get(tier, settings.TIER_LIMITS["FREE"])

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
