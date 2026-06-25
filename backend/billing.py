import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models as DBmodels
from core.database import async_session_factory, get_db
from security import redis_client, get_subscription_plan, get_current_user
from core.config import settings

logger = logging.getLogger("quantcai.billing")

# Default success/cancel URLs derived from frontend origin
FRONTEND_URL = settings.FRONTEND_URL.split(",")[0]


# -----------------------------------------------------------------------------
# FastAPI Router Setup
# -----------------------------------------------------------------------------
router = APIRouter(prefix="/api/billing", tags=["Billing & Subscriptions"])

@router.get("/status")
async def get_subscription_status(
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current user's active subscription tier."""
    plan = await get_subscription_plan(db, current_user.id, current_user.org_id)
    return {
        "tier": plan.upper(),
        "status": "active" if plan != "free" else "inactive"
    }

# -----------------------------------------------------------------------------
# Redis Caching Helpers
# -----------------------------------------------------------------------------
async def clear_feature_access_cache(user_id: int):
    """
    Invalidates the Redis cache for all feature access checks for the given user.
    """
    try:
        features = ["ai_tutor_pro", "pqc_scan", "api_access", "cbom_export"]
        keys = [f"feature_access:{user_id}:{feature}" for feature in features]
        await redis_client.delete(*keys)
        logger.info(f"Cleared feature access Redis cache for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to clear Redis feature access cache for user {user_id}: {e}", exc_info=True)

# -----------------------------------------------------------------------------
# Price & Plan Helpers
# -----------------------------------------------------------------------------
def map_string_to_plan(plan_str: Optional[str]) -> DBmodels.SubscriptionPlan:
    """Map plain plan name string to SubscriptionPlan enum."""
    if not plan_str:
        return DBmodels.SubscriptionPlan.FREE
    plan_str_lower = plan_str.lower()
    if "pro" in plan_str_lower:
        return DBmodels.SubscriptionPlan.PRO
    if "enterprise" in plan_str_lower:
        return DBmodels.SubscriptionPlan.ENTERPRISE
    return DBmodels.SubscriptionPlan.FREE

async def check_feature_access(
    user: DBmodels.User,
    feature: str,
    db: Optional[AsyncSession] = None
) -> bool:
    """
    Check if a user has access to a specific feature based on their active plan.
    Feature options: "ai_tutor_pro", "pqc_scan", "api_access", "cbom_export"
    
    Caches the access result in Redis for 300 seconds.
    """
    valid_features = {"ai_tutor_pro", "pqc_scan", "api_access", "cbom_export"}
    if feature not in valid_features:
        logger.warning(f"Invalid feature query: '{feature}'")
        return False

    cache_key = f"feature_access:{user.id}:{feature}"

    # 1. Check Redis cache
    try:
        cached_val = await redis_client.get(cache_key)
        if cached_val is not None:
            return cached_val == "true"
    except Exception as e:
        logger.error(f"Redis cache lookup failed: {e}", exc_info=True)

    # 2. Retrieve user subscription status
    plan = "free"
    try:
        if db is not None:
            plan = await get_subscription_plan(db, user.id, user.org_id)
        else:
            async with async_session_factory() as session:
                plan = await get_subscription_plan(session, user.id, user.org_id)
    except Exception as e:
        logger.error(f"Database lookup failed for user subscription: {e}", exc_info=True)
        plan = "free"

    # Normalize plan value
    plan_lower = plan.lower() if plan else "free"

    # 3. Assess access rights
    # - Free: "pqc_scan", "api_access"
    # - Pro: "ai_tutor_pro", "pqc_scan", "api_access"
    # - Enterprise: "ai_tutor_pro", "pqc_scan", "api_access", "cbom_export"
    has_access = False
    if plan_lower == "enterprise":
        has_access = True
    elif plan_lower == "pro":
        has_access = feature in {"ai_tutor_pro", "pqc_scan", "api_access"}
    elif plan_lower in {"free", "starter"}:
        has_access = feature in {"pqc_scan", "api_access"}

    # 4. Cache response
    try:
        await redis_client.setex(cache_key, 300, "true" if has_access else "false")
    except Exception as e:
        logger.error(f"Redis cache write failed: {e}", exc_info=True)

    return has_access

# -----------------------------------------------------------------------------
# End of File
# -----------------------------------------------------------------------------

