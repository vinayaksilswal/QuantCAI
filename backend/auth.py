import os
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

import models as DBmodels
from core.database import get_db
from security import (
    generate_api_key,
    hash_api_key,
    get_subscription_plan,
    get_current_user
)

router = APIRouter(tags=["Authentication & Keys"])
logger = logging.getLogger("quantcai.api_keys")

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------


class APIKeyCreateRequest(BaseModel):
    label: str

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.post("/developer/keys")
async def create_developer_key(
    key_data: APIKeyCreateRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new API key, store its hash, and return the plaintext key ONCE.
    """
    # Verify user's subscription tier
    user_plan = await get_subscription_plan(db, current_user.id, current_user.org_id)
    
    # Map subscription plan to APIKeyTier enum
    tier_map = {
        "free": DBmodels.APIKeyTier.FREE,
        "pro": DBmodels.APIKeyTier.PRO,
        "enterprise": DBmodels.APIKeyTier.ENTERPRISE
    }
    api_key_tier = tier_map.get(user_plan, DBmodels.APIKeyTier.FREE)

    # Define daily request limits per tier
    limit_map = {
        DBmodels.APIKeyTier.FREE: 1000,
        DBmodels.APIKeyTier.PRO: 10000,
        DBmodels.APIKeyTier.ENTERPRISE: 100000
    }
    daily_limit = limit_map[api_key_tier]
    
    # Count existing keys efficiently
    stmt = select(func.count()).select_from(DBmodels.APIKey).where(DBmodels.APIKey.user_id == current_user.id)
    res = await db.execute(stmt)
    existing_keys = res.scalar_one() or 0
    
    max_keys = 20 if user_plan in ["pro", "enterprise"] else 5
    if existing_keys >= max_keys:
        raise HTTPException(status_code=400, detail=f"Maximum API keys ({max_keys}) reached for your tier.")

    # Generate key pair
    plaintext_key = generate_api_key()
    hashed_key = hash_api_key(plaintext_key)

    new_api_key = DBmodels.APIKey(
        user_id=current_user.id,
        key_hash=hashed_key,
        label=key_data.label,
        tier=api_key_tier,
        daily_limit=daily_limit,
        is_active=True,
        requests_today=0
    )
    
    db.add(new_api_key)
    await db.commit()
    await db.refresh(new_api_key)

    logger.info(f"AUDIT: User {current_user.id} created API key '{key_data.label}' (Tier: {api_key_tier.value})")

    return {
        "id": new_api_key.id,
        "label": new_api_key.label,
        "tier": new_api_key.tier.value if hasattr(new_api_key.tier, "value") else str(new_api_key.tier),
        "daily_limit": new_api_key.daily_limit,
        "is_active": new_api_key.is_active,
        "requests_today": new_api_key.requests_today,
        "api_key": plaintext_key  # Plaintext key returned ONCE
    }

@router.get("/developer/keys")
async def list_developer_keys(
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all API keys belonging to the current authenticated user.
    """
    stmt = select(DBmodels.APIKey).where(DBmodels.APIKey.user_id == current_user.id)
    res = await db.execute(stmt)
    keys = res.scalars().all()
    return [
        {
            "id": k.id,
            "label": k.label,
            "tier": k.tier.value if hasattr(k.tier, "value") else str(k.tier),
            "requests_today": k.requests_today,
            "daily_limit": k.daily_limit,
            "last_used": k.last_used_at.isoformat() if k.last_used_at else None,
            "is_active": k.is_active
        }
        for k in keys
    ]

@router.delete("/developer/keys/{key_id}")
async def delete_developer_key(
    key_id: int,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an API key belonging to the current authenticated user.
    """
    stmt = select(DBmodels.APIKey).where(
        (DBmodels.APIKey.id == key_id) & (DBmodels.APIKey.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    key = res.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found or access denied")
    
    await db.delete(key)
    await db.commit()
    
    logger.info(f"AUDIT: User {current_user.id} deleted API key ID {key_id}")
    return {"message": "API key deleted successfully"}


@router.post("/developer/keys/{key_id}/rotate")
async def rotate_developer_key(
    key_id: int,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Rotate an API key: generates a new key string but keeps the same ID, label, and limits.
    Invalidates the old key immediately.
    """
    stmt = select(DBmodels.APIKey).where(
        (DBmodels.APIKey.id == key_id) & (DBmodels.APIKey.user_id == current_user.id)
    ).with_for_update()
    res = await db.execute(stmt)
    key = res.scalar_one_or_none()
    
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found or access denied")
    
    # Generate new key pair
    plaintext_key = generate_api_key()
    hashed_key = hash_api_key(plaintext_key)
    
    key.key_hash = hashed_key
    db.add(key)
    await db.commit()
    
    logger.info(f"AUDIT: User {current_user.id} rotated API key ID {key_id}")
    
    return {
        "message": "API key rotated successfully",
        "api_key": plaintext_key  # Plaintext key returned ONCE
    }
