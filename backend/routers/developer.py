import secrets
import hashlib
import logging
import json
import httpx
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
from core.config import settings
from routers.paypal_billing import _get_paypal_access_token, _paypal_base_url

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
    amount: float  # Amount in USD

class CaptureRequest(BaseModel):
    order_id: str

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

@router.post("/wallet/topup")
async def topup_wallet(
    body: TopupRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a PayPal Order for developer wallet top-up."""
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Topup amount must be positive")
        
    access_token = await _get_paypal_access_token()
    frontend_url = settings.FRONTEND_URL.split(",")[0]
    
    order_payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "USD",
                    "value": f"{body.amount:.2f}"
                },
                "description": f"QuantCAI Developer Wallet Topup - User ID {current_user.id}"
            }
        ],
        "application_context": {
            "brand_name": "QuantCAI",
            "locale": "en-US",
            "user_action": "PAY_NOW",
            "return_url": f"{frontend_url}/profile?topup=success",
            "cancel_url": f"{frontend_url}/profile?topup=cancel"
        }
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_paypal_base_url()}/v2/checkout/orders",
            json=order_payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=20.0
        )
        
    if resp.status_code not in (200, 201):
        logger.error(f"PayPal Order creation failed: {resp.status_code} {resp.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to initiate PayPal payment."
        )
        
    order_data = resp.json()
    approval_url = None
    for link in order_data.get("links", []):
        if link.get("rel") == "approve":
            approval_url = link.get("href")
            break
            
    if not approval_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="PayPal did not return an approval URL."
        )
        
    return {
        "url": approval_url,
        "order_id": order_data.get("id")
    }

@router.post("/wallet/capture", response_model=WalletResponse)
async def capture_wallet_topup(
    body: CaptureRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Capture a PayPal order and credit the user's wallet balance."""
    # Prevent duplicate captures (replay protection)
    cache_captured_key = f"developer:captured_orders:{body.order_id}"
    already_captured = await redis_client.get(cache_captured_key)
    if already_captured:
        raise HTTPException(
            status_code=400,
            detail="This transaction has already been captured and processed."
        )

    access_token = await _get_paypal_access_token()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_paypal_base_url()}/v2/checkout/orders/{body.order_id}/capture",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=20.0
        )

    if resp.status_code not in (200, 201):
        # Check if already captured on PayPal (fallback in case of API failure / client retry)
        async with httpx.AsyncClient() as check_client:
            check_resp = await check_client.get(
                f"{_paypal_base_url()}/v2/checkout/orders/{body.order_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=15.0
            )
        
        if check_resp.status_code == 200:
            order_details = check_resp.json()
            if order_details.get("status") == "COMPLETED":
                purchase_units = order_details.get("purchase_units", [])
                amount_val = float(purchase_units[0]["amount"]["value"]) if purchase_units else 0.0
                return await _credit_user_wallet(db, current_user.id, amount_val, body.order_id)
        
        logger.error(f"PayPal capture request failed: {resp.status_code} {resp.text}")
        raise HTTPException(
            status_code=502,
            detail="Failed to capture payment with PayPal. Please check order status."
        )

    capture_data = resp.json()
    status_str = capture_data.get("status")
    
    if status_str != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail=f"PayPal transaction status is '{status_str}', not 'COMPLETED'."
        )

    # Find the amount captured
    purchase_units = capture_data.get("purchase_units", [])
    amount_val = 0.0
    if purchase_units:
        payments = purchase_units[0].get("payments", {})
        captures = payments.get("captures", [])
        if captures:
            amount_val = float(captures[0]["amount"]["value"])
            
    if amount_val <= 0:
        raise HTTPException(
            status_code=400,
            detail="No valid capture amount found in PayPal transaction."
        )

    return await _credit_user_wallet(db, current_user.id, amount_val, body.order_id)

async def _credit_user_wallet(db: AsyncSession, user_id: int, amount: float, order_id: str):
    stmt = select(WalletBalance).where(WalletBalance.user_id == user_id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()
    
    if not wallet:
        wallet = WalletBalance(user_id=user_id, balance_credits=0.0, auto_topup_enabled=False)
        
    wallet.balance_credits = float(wallet.balance_credits) + amount
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)

    # Store order ID in Redis to prevent replay
    cache_captured_key = f"developer:captured_orders:{order_id}"
    await redis_client.setex(cache_captured_key, 86400 * 30, "1")  # cache for 30 days
    
    # Sync with Redis cache & remove block flag
    wallet_cache_key = f"developer:wallet:{user_id}"
    await redis_client.set(wallet_cache_key, str(wallet.balance_credits))
    await redis_client.delete(f"developer:wallet_blocked:{user_id}")
    
    logger.info(f"Developer wallet credited: user_id={user_id}, amount=${amount:.2f}, order_id={order_id}")
    
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
