"""
PayPal Wallet Top-Up Router
===================================
Handles one-time PayPal payments for adding developer API credits to the user's wallet.
Uses PayPal REST API v2 (Orders API).

Replaces the previous subscription-based PayPal integration.
"""

import logging
import httpx
import json
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models as DBmodels
from core.database import get_db
from core.config import settings
from core.auth import get_current_user
from security import redis_client

logger = logging.getLogger("quantcai.paypal_wallet")

router = APIRouter(prefix="/api/billing/wallet", tags=["Wallet Top-up"])

# ---------------------------------------------------------------------------
# PayPal API Configuration & Helpers
# ---------------------------------------------------------------------------
def _paypal_base_url() -> str:
    if settings.PAYPAL_MODE == "live":
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"


async def _get_paypal_access_token() -> str:
    """Obtain and cache PayPal OAuth2 access token."""
    cache_key = "paypal_access_token"
    cached_token = await redis_client.get(cache_key)
    if cached_token:
        return cached_token

    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PayPal wallet top-up is not configured on this server."
        )

    url = f"{_paypal_base_url()}/v1/oauth2/token"
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)

    # Use a connection pool for better performance (simulate by sharing client if possible, but context manager is fine for now)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=auth,
            headers={"Accept": "application/json"},
            timeout=15.0,
        )

    if resp.status_code != 200:
        logger.error(f"PayPal OAuth2 token request failed: {resp.status_code} {resp.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to authenticate with PayPal."
        )

    data = resp.json()
    token = data["access_token"]
    expires_in = int(data.get("expires_in", 32400))  # Usually 9 hours

    # Cache token with TTL slightly less than expiry
    await redis_client.setex(cache_key, max(1, expires_in - 300), token)
    return token


async def _get_or_create_wallet(db: AsyncSession, user_id: int) -> DBmodels.WalletBalance:
    """Get the user's wallet, creating one if it doesn't exist."""
    stmt = select(DBmodels.WalletBalance).where(DBmodels.WalletBalance.user_id == user_id).with_for_update()
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()

    if not wallet:
        wallet = DBmodels.WalletBalance(user_id=user_id, balance=0.0)
        db.add(wallet)
        await db.flush()
    return wallet


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------
class TopUpRequest(BaseModel):
    amount: int  # Must be one of the allowed amounts in settings.PAYPAL_WALLET_TOPUP_AMOUNTS
    return_url: str | None = None
    cancel_url: str | None = None


class CaptureRequest(BaseModel):
    order_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/balance")
async def get_wallet_balance(
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current wallet balance."""
    stmt = select(DBmodels.WalletBalance.balance).where(DBmodels.WalletBalance.user_id == current_user.id)
    res = await db.execute(stmt)
    balance = res.scalar_one_or_none() or 0.0
    return {"balance": balance}


@router.post("/topup")
async def create_topup_order(
    body: TopUpRequest,
    current_user: DBmodels.User = Depends(get_current_user),
):
    """
    Step 1: Create a PayPal order for a specific amount.
    Returns the PayPal approval URL for the frontend to redirect the user.
    """
    if body.amount not in settings.wallet_topup_amounts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid amount. Allowed amounts: {settings.wallet_topup_amounts}"
        )

    access_token = await _get_paypal_access_token()
    
    frontend_url = settings.FRONTEND_URL.split(",")[0]
    return_url = body.return_url or f"{frontend_url}/developer?topup=success"
    cancel_url = body.cancel_url or f"{frontend_url}/developer?topup=cancelled"

    order_payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": f"wallet_{current_user.id}_{int(datetime.now().timestamp())}",
                "description": f"QuantCAI Developer API Credits - ${body.amount}",
                "amount": {
                    "currency_code": "USD",
                    "value": f"{body.amount}.00"
                },
                "custom_id": str(current_user.id)
            }
        ],
        "application_context": {
            "brand_name": "QuantCAI",
            "locale": "en-US",
            "shipping_preference": "NO_SHIPPING",
            "user_action": "PAY_NOW",
            "return_url": return_url,
            "cancel_url": cancel_url
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
            timeout=20.0,
        )

    if resp.status_code not in (200, 201):
        logger.error(f"PayPal order creation failed: {resp.status_code} {resp.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create PayPal checkout session."
        )

    data = resp.json()
    order_id = data.get("id")
    
    approval_url = None
    for link in data.get("links", []):
        if link.get("rel") == "approve":
            approval_url = link.get("href")
            break

    if not approval_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="PayPal did not return an approval URL."
        )

    return {
        "order_id": order_id,
        "url": approval_url
    }


@router.post("/capture")
async def capture_topup_order(
    body: CaptureRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Step 2: Capture the PayPal order after user approval.
    Idempotent operation that credits the user's wallet.
    """
    # 1. Idempotency Check
    idempotency_key = f"wallet_topup:{body.order_id}"
    already_processed = await redis_client.set(idempotency_key, "1", nx=True, ex=86400 * 7) # Keep for 7 days
    
    if not already_processed:
        # Check DB to see if already credited
        stmt = select(DBmodels.WalletTransaction).where(DBmodels.WalletTransaction.reference_id == f"paypal_{body.order_id}")
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            return {"status": "ok", "message": "Order already captured and credited."}
        # If not in DB, allow retry by deleting redis key
        await redis_client.delete(idempotency_key)

    # 2. Capture Payment on PayPal
    access_token = await _get_paypal_access_token()
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_paypal_base_url()}/v2/checkout/orders/{body.order_id}/capture",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=20.0,
        )

    # If already captured, PayPal returns 422 with issue=ORDER_ALREADY_CAPTURED.
    # We should query the order status to verify.
    if resp.status_code == 422 and "ORDER_ALREADY_CAPTURED" in resp.text:
        # Query order to get capture details
        async with httpx.AsyncClient() as client_get:
            get_resp = await client_get.get(
                f"{_paypal_base_url()}/v2/checkout/orders/{body.order_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        if get_resp.status_code == 200:
            capture_data = get_resp.json()
        else:
            await redis_client.delete(idempotency_key)
            raise HTTPException(status_code=502, detail="Failed to verify captured order status.")
    elif resp.status_code not in (200, 201):
        await redis_client.delete(idempotency_key)
        logger.error(f"PayPal capture failed: {resp.status_code} {resp.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to capture payment. Please try again."
        )
    else:
        capture_data = resp.json()

    # 3. Extract amount and verify it matches user
    try:
        purchase_unit = capture_data.get("purchase_units", [])[0]
        custom_id = purchase_unit.get("custom_id")
        
        # Verify the order belongs to this user
        if custom_id and str(custom_id) != str(current_user.id):
            logger.error(f"Order {body.order_id} belongs to user {custom_id}, not {current_user.id}")
            raise HTTPException(status_code=403, detail="Order does not belong to you.")
            
        captures = purchase_unit.get("payments", {}).get("captures", [])
        if not captures:
            raise ValueError("No captures found in order.")
            
        capture = captures[0]
        if capture.get("status") != "COMPLETED":
            raise ValueError(f"Capture status is not COMPLETED (got {capture.get('status')}).")
            
        amount_str = capture.get("amount", {}).get("value", "0")
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
            
    except Exception as e:
        await redis_client.delete(idempotency_key)
        logger.error(f"Error parsing capture data for order {body.order_id}: {e}")
        raise HTTPException(status_code=400, detail="Invalid capture data received from PayPal.")

    # 4. Credit Wallet & Record Transaction
    wallet = await _get_or_create_wallet(db, current_user.id)
    
    # Check one more time inside lock to be absolutely safe against race conditions
    stmt_tx = select(DBmodels.WalletTransaction).where(DBmodels.WalletTransaction.reference_id == f"paypal_{body.order_id}")
    res_tx = await db.execute(stmt_tx)
    if res_tx.scalar_one_or_none():
        return {"status": "ok", "message": "Already credited."}

    wallet.balance += amount
    
    transaction = DBmodels.WalletTransaction(
        wallet_id=wallet.id,
        amount=amount,
        transaction_type=DBmodels.TransactionType.CREDIT,
        description=f"PayPal Wallet Top-up",
        reference_id=f"paypal_{body.order_id}"
    )
    
    db.add(wallet)
    db.add(transaction)
    await db.commit()
    
    logger.info(f"Wallet top-up successful: user={current_user.id}, amount=${amount}, order={body.order_id}")
    
    return {
        "status": "success",
        "new_balance": wallet.balance,
        "amount_added": amount
    }

@router.get("/history")
async def get_wallet_history(
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50
):
    """Get user's wallet transaction history."""
    wallet = await _get_or_create_wallet(db, current_user.id)
    
    stmt = (
        select(DBmodels.WalletTransaction)
        .where(DBmodels.WalletTransaction.wallet_id == wallet.id)
        .order_by(DBmodels.WalletTransaction.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    transactions = res.scalars().all()
    
    return [
        {
            "id": tx.id,
            "amount": tx.amount,
            "type": tx.transaction_type.value,
            "description": tx.description,
            "date": tx.created_at.isoformat()
        }
        for tx in transactions
    ]
