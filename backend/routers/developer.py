import secrets
import hashlib
import logging
import json
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

import models as DBmodels
from core.database import get_db
from security import get_current_user, redis_client
from models_billing import ApiKey, WalletBalance, DailyUsageRollup

logger = logging.getLogger("quantcai.routers.developer")
router = APIRouter(prefix="/api/v1/developer", tags=["Developer portal & Billing"])

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------
class KeyCreateRequest(BaseModel):
    name: str

class KeyPatchRequest(BaseModel):
    is_active: bool

class TopupRequest(BaseModel):
    amount: float  # Amount in cents / paise

class WalletPatchRequest(BaseModel):
    auto_topup_enabled: bool

class KeyResponse(BaseModel):
    id: int
    name: str
    prefix: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True

class WalletResponse(BaseModel):
    balance_credits: float
    auto_topup_enabled: bool

class DailyUsageResponse(BaseModel):
    date: str
    requests: int
    shots: int
    spend: float

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/keys", response_model=List[KeyResponse])
async def list_keys(
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all developer API keys belonging to the current user."""
    stmt = select(ApiKey).where(ApiKey.user_id == current_user.id).order_by(ApiKey.created_at.desc())
    res = await db.execute(stmt)
    keys = res.scalars().all()
    
    return [
        KeyResponse(
            id=k.id,
            name=k.name,
            prefix=k.prefix,
            is_active=k.is_active,
            created_at=k.created_at.isoformat()
        )
        for k in keys
    ]

@router.post("/keys")
async def create_key(
    body: KeyCreateRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a new developer API key and return the raw plaintext key ONCE."""
    # Prefix format: qc_live_
    raw_key = f"qc_live_{secrets.token_urlsafe(32)}"
    hashed_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    
    new_key = ApiKey(
        user_id=current_user.id,
        hashed_key=hashed_key,
        prefix="qc_live_",
        name=body.name,
        is_active=True
    )
    
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    
    # Cache key details in Redis for fast validation
    cache_key = f"developer:apikey:{hashed_key}"
    key_info = {
        "id": new_key.id,
        "user_id": new_key.user_id,
        "prefix": new_key.prefix,
        "name": new_key.name,
        "is_active": new_key.is_active
    }
    await redis_client.setex(cache_key, 600, json.dumps(key_info))
    
    return {
        "id": new_key.id,
        "name": new_key.name,
        "prefix": new_key.prefix,
        "is_active": new_key.is_active,
        "created_at": new_key.created_at.isoformat(),
        "api_key": raw_key  # Returned raw plaintext only once
    }

@router.patch("/keys/{key_id}", response_model=KeyResponse)
async def update_key(
    key_id: int,
    body: KeyPatchRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Activate or deactivate a developer API key."""
    stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    res = await db.execute(stmt)
    key = res.scalar_one_or_none()
    
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    key.is_active = body.is_active
    db.add(key)
    await db.commit()
    await db.refresh(key)
    
    # Invalidate Redis cache
    cache_key = f"developer:apikey:{key.hashed_key}"
    await redis_client.delete(cache_key)
    
    return KeyResponse(
        id=key.id,
        name=key.name,
        prefix=key.prefix,
        is_active=key.is_active,
        created_at=key.created_at.isoformat()
    )

@router.delete("/keys/{key_id}")
async def delete_key(
    key_id: int,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Permanently delete a developer API key."""
    stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    res = await db.execute(stmt)
    key = res.scalar_one_or_none()
    
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    hashed_key = key.hashed_key
    await db.delete(key)
    await db.commit()
    
    # Invalidate Redis cache
    cache_key = f"developer:apikey:{hashed_key}"
    await redis_client.delete(cache_key)
    
    return {"status": "success", "message": "API Key permanently deleted"}

@router.get("/wallet", response_model=WalletResponse)
async def get_wallet(
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the user's current wallet balance and auto-topup configuration."""
    stmt = select(WalletBalance).where(WalletBalance.user_id == current_user.id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()
    
    if not wallet:
        wallet = WalletBalance(user_id=current_user.id, balance_credits=0.0, auto_topup_enabled=False)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
        
    # Sync cache in Redis
    wallet_cache_key = f"developer:wallet:{current_user.id}"
    await redis_client.set(wallet_cache_key, str(wallet.balance_credits))
    
    return WalletResponse(
        balance_credits=float(wallet.balance_credits),
        auto_topup_enabled=wallet.auto_topup_enabled
    )

@router.post("/wallet/topup", response_model=WalletResponse)
async def topup_wallet(
    body: TopupRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Simulate credit topup via Stripe/Razorpay hook. Increments balance directly."""
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Topup amount must be positive")
        
    stmt = select(WalletBalance).where(WalletBalance.user_id == current_user.id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()
    
    if not wallet:
        wallet = WalletBalance(user_id=current_user.id, balance_credits=0.0, auto_topup_enabled=False)
        
    wallet.balance_credits = float(wallet.balance_credits) + body.amount
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    
    # Update Redis cache & remove block flag
    wallet_cache_key = f"developer:wallet:{current_user.id}"
    await redis_client.set(wallet_cache_key, str(wallet.balance_credits))
    await redis_client.delete(f"developer:wallet_blocked:{current_user.id}")
    
    return WalletResponse(
        balance_credits=float(wallet.balance_credits),
        auto_topup_enabled=wallet.auto_topup_enabled
    )

@router.patch("/wallet", response_model=WalletResponse)
async def update_wallet(
    body: WalletPatchRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle auto-topup settings."""
    stmt = select(WalletBalance).where(WalletBalance.user_id == current_user.id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()
    
    if not wallet:
        wallet = WalletBalance(user_id=current_user.id, balance_credits=0.0, auto_topup_enabled=False)
        
    wallet.auto_topup_enabled = body.auto_topup_enabled
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    
    return WalletResponse(
        balance_credits=float(wallet.balance_credits),
        auto_topup_enabled=wallet.auto_topup_enabled
    )

@router.get("/usage", response_model=List[DailyUsageResponse])
async def get_usage(
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve rollup of daily consumption and spend over rolling 30-day timeline."""
    stmt = (
        select(
            DailyUsageRollup.usage_date,
            func.sum(DailyUsageRollup.requests_count).label("requests"),
            func.sum(DailyUsageRollup.total_shots).label("shots"),
            func.sum(DailyUsageRollup.total_spend).label("spend")
        )
        .join(ApiKey)
        .where(ApiKey.user_id == current_user.id)
        .group_by(DailyUsageRollup.usage_date)
        .order_by(DailyUsageRollup.usage_date.asc())
        .limit(30)
    )
    
    res = await db.execute(stmt)
    rows = res.all()
    
    # If there are no rows, return mock data for rolling 30 days to make the first-load look beautiful
    if not rows:
        today = datetime.now(timezone.utc)
        mock_data = []
        for i in range(29, -1, -1):
            date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            # Generate a nice curve
            mock_data.append(DailyUsageResponse(
                date=date_str,
                requests=0,
                shots=0,
                spend=0.0
            ))
        return mock_data
        
    return [
        DailyUsageResponse(
            date=row.usage_date,
            requests=row.requests,
            shots=row.shots,
            spend=float(row.spend)
        )
        for row in rows
    ]
