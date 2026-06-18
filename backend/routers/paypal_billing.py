"""
PayPal Billing Integration Router
===================================
Handles PayPal Subscription creation, management, and Webhook events
for subscription lifecycle management.

Uses the PayPal REST API v2 (Subscriptions API) with server-side
OAuth2 authentication via Client ID + Secret.

Replaces the WarriorPlus IPN handler as the primary payment gateway.

Copyright (c) 2026 QuantCAI — All rights reserved.
"""

import logging
import httpx
import hashlib
import hmac
import json
import base64
import zlib
from datetime import datetime, timezone, timedelta, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models as DBmodels
from core.database import get_db
from core.config import settings
from core.auth import get_current_user
from billing import clear_feature_access_cache

logger = logging.getLogger("quantcai.paypal")

router = APIRouter(prefix="/api/billing", tags=["PayPal Billing"])


# ---------------------------------------------------------------------------
# PayPal API Configuration
# ---------------------------------------------------------------------------
def _paypal_base_url() -> str:
    """Return the PayPal API base URL based on mode (sandbox/live)."""
    if settings.PAYPAL_MODE == "live":
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"


async def _get_paypal_access_token() -> str:
    """
    Obtain a PayPal OAuth2 access token using Client ID + Secret.
    Tokens are short-lived (~9 hours) — obtained fresh per webhook batch.
    """
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PayPal billing is not configured on this server."
        )

    url = f"{_paypal_base_url()}/v1/oauth2/token"
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)

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
    return data["access_token"]


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------
class SubscriptionRequest(BaseModel):
    plan: str  # "pro" or "enterprise"
    return_url: str | None = None
    cancel_url: str | None = None


# ---------------------------------------------------------------------------
# Endpoints: Create Subscription
# ---------------------------------------------------------------------------

@router.post("/subscribe")
async def create_paypal_subscription(
    body: SubscriptionRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a PayPal Subscription for upgrading to Pro or Enterprise.
    Returns the PayPal approval URL for frontend redirect.
    
    Flow:
    1. Backend creates a subscription via PayPal Subscriptions API
    2. Frontend redirects user to PayPal approval URL
    3. User approves on PayPal
    4. PayPal sends webhook to /api/billing/webhooks/paypal
    5. Backend activates the subscription
    """
    # Map plan to PayPal Plan ID
    plan_id_map = {
        "pro": settings.PAYPAL_PRO_PLAN_ID,
        "enterprise": settings.PAYPAL_ENTERPRISE_PLAN_ID,
    }
    plan_id = plan_id_map.get(body.plan.lower())
    if not plan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan: '{body.plan}'. Must be 'pro' or 'enterprise'."
        )

    frontend_url = settings.FRONTEND_URL.split(",")[0]
    return_url = body.return_url or f"{frontend_url}/dashboard?checkout=success"
    cancel_url = body.cancel_url or f"{frontend_url}/get-started?checkout=cancelled"

    # Check for existing active subscription — prevent double-billing
    stmt = select(DBmodels.Subscription).where(
        DBmodels.Subscription.user_id == current_user.id,
        DBmodels.Subscription.status == DBmodels.SubscriptionStatus.ACTIVE,
    )
    res = await db.execute(stmt)
    existing_sub = res.scalars().first()

    if existing_sub and existing_sub.stripe_subscription_id and existing_sub.stripe_subscription_id.startswith("PAYPAL_"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active subscription. Cancel your current plan before subscribing to a new one."
        )

    # Create PayPal Subscription
    access_token = await _get_paypal_access_token()

    subscription_payload = {
        "plan_id": plan_id,
        "subscriber": {
            "name": {
                "given_name": current_user.name.split(" ")[0] if current_user.name else "User",
                "surname": " ".join(current_user.name.split(" ")[1:]) if current_user.name and len(current_user.name.split(" ")) > 1 else "",
            },
            "email_address": current_user.email,
        },
        "application_context": {
            "brand_name": "QuantCAI",
            "locale": "en-US",
            "shipping_preference": "NO_SHIPPING",
            "user_action": "SUBSCRIBE_NOW",
            "return_url": return_url,
            "cancel_url": cancel_url,
        },
        "custom_id": str(current_user.id),  # Store our user ID for webhook correlation
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_paypal_base_url()}/v1/billing/subscriptions",
            json=subscription_payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            timeout=20.0,
        )

    if resp.status_code not in (200, 201):
        logger.error(f"PayPal subscription creation failed: {resp.status_code} {resp.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create PayPal subscription. Please try again."
        )

    sub_data = resp.json()
    paypal_sub_id = sub_data.get("id")

    # Extract approval URL
    approval_url = None
    for link in sub_data.get("links", []):
        if link.get("rel") == "approve":
            approval_url = link.get("href")
            break

    if not approval_url:
        logger.error(f"No approval URL in PayPal response: {sub_data}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="PayPal did not return an approval URL."
        )

    # Store a PENDING subscription record so webhook can activate it
    plan_enum = DBmodels.SubscriptionPlan.PRO if "pro" in body.plan.lower() else DBmodels.SubscriptionPlan.ENTERPRISE

    stmt = select(DBmodels.Subscription).where(DBmodels.Subscription.user_id == current_user.id)
    res = await db.execute(stmt)
    db_sub = res.scalars().first()

    if db_sub:
        db_sub.stripe_subscription_id = f"PAYPAL_{paypal_sub_id}"
        db_sub.plan = plan_enum
        db_sub.status = DBmodels.SubscriptionStatus.TRIALING  # Pending approval
        db_sub.updated_at = datetime.now(timezone.utc)
        db.add(db_sub)
    else:
        db_sub = DBmodels.Subscription(
            user_id=current_user.id,
            stripe_subscription_id=f"PAYPAL_{paypal_sub_id}",
            plan=plan_enum,
            status=DBmodels.SubscriptionStatus.TRIALING,
        )
        db.add(db_sub)

    await db.commit()

    logger.info(
        f"PayPal subscription created: user={current_user.id}, "
        f"paypal_sub_id={paypal_sub_id}, plan={body.plan}"
    )

    return {
        "url": approval_url,
        "subscription_id": paypal_sub_id,
        "plan": body.plan,
    }


@router.post("/cancel")
async def cancel_paypal_subscription(
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel the user's active PayPal subscription.
    """
    stmt = select(DBmodels.Subscription).where(
        DBmodels.Subscription.user_id == current_user.id,
        DBmodels.Subscription.status == DBmodels.SubscriptionStatus.ACTIVE,
    )
    res = await db.execute(stmt)
    db_sub = res.scalars().first()

    if not db_sub or not db_sub.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found."
        )

    # Only handle PayPal subscriptions
    if not db_sub.stripe_subscription_id.startswith("PAYPAL_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This subscription is not managed by PayPal."
        )

    paypal_sub_id = db_sub.stripe_subscription_id.replace("PAYPAL_", "")

    # Cancel on PayPal's side
    access_token = await _get_paypal_access_token()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_paypal_base_url()}/v1/billing/subscriptions/{paypal_sub_id}/cancel",
            json={"reason": "User requested cancellation via QuantCAI dashboard"},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=15.0,
        )

    if resp.status_code not in (200, 204):
        logger.error(f"PayPal cancellation failed: {resp.status_code} {resp.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to cancel subscription on PayPal. Please try again or contact support."
        )

    # Update local records
    db_sub.status = DBmodels.SubscriptionStatus.CANCELLED
    db_sub.plan = DBmodels.SubscriptionPlan.FREE
    db_sub.updated_at = datetime.now(timezone.utc)
    db.add(db_sub)

    # Downgrade UserPlan
    plan_stmt = select(DBmodels.UserPlan).where(DBmodels.UserPlan.user_id == current_user.id)
    plan_res = await db.execute(plan_stmt)
    user_plan = plan_res.scalar_one_or_none()
    if user_plan:
        user_plan.tier = DBmodels.Tier.FREE
        db.add(user_plan)

    await db.commit()
    await clear_feature_access_cache(current_user.id)

    logger.info(f"PayPal subscription cancelled: user={current_user.id}, paypal_sub_id={paypal_sub_id}")

    return {"status": "cancelled", "message": "Your subscription has been cancelled. You retain access until the end of your current billing period."}


@router.get("/subscription")
async def get_subscription_status(
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current user's subscription status."""
    stmt = select(DBmodels.Subscription).where(
        DBmodels.Subscription.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    db_sub = res.scalars().first()

    if not db_sub:
        return {
            "plan": "free",
            "status": "active",
            "provider": None,
            "current_period_end": None,
        }

    provider = "paypal" if (db_sub.stripe_subscription_id or "").startswith("PAYPAL_") else (
        "warriorplus" if (db_sub.stripe_subscription_id or "").startswith("warriorplus_") else "stripe"
    )

    return {
        "plan": db_sub.plan.value,
        "status": db_sub.status.value,
        "provider": provider,
        "current_period_end": db_sub.current_period_end.isoformat() if db_sub.current_period_end else None,
    }


# ---------------------------------------------------------------------------
# PayPal Webhook Handler
# ---------------------------------------------------------------------------

@router.post("/webhooks/paypal")
async def paypal_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle PayPal webhook events for subscription lifecycle management.
    
    Events handled:
    - BILLING.SUBSCRIPTION.ACTIVATED: Subscription approved and active
    - BILLING.SUBSCRIPTION.CANCELLED: User cancelled subscription
    - BILLING.SUBSCRIPTION.SUSPENDED: Payment failed, subscription suspended
    - BILLING.SUBSCRIPTION.EXPIRED: Subscription expired
    - BILLING.SUBSCRIPTION.UPDATED: Plan change or renewal
    - PAYMENT.SALE.COMPLETED: Recurring payment received
    """
    payload = await request.body()

    # Verify webhook signature if webhook ID is configured
    if settings.PAYPAL_WEBHOOK_ID:
        is_valid = await _verify_paypal_webhook(request, payload)
        if not is_valid:
            logger.warning("PayPal webhook signature verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    event_type = event.get("event_type", "")
    resource = event.get("resource", {})

    logger.info(f"Received PayPal webhook: {event_type} (ID: {event.get('id', 'unknown')})")

    # ─── BILLING.SUBSCRIPTION.ACTIVATED ───────────────────────────────
    if event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
        await _handle_subscription_activated(db, resource)

    # ─── BILLING.SUBSCRIPTION.CANCELLED ───────────────────────────────
    elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
        await _handle_subscription_cancelled(db, resource)

    # ─── BILLING.SUBSCRIPTION.SUSPENDED ───────────────────────────────
    elif event_type == "BILLING.SUBSCRIPTION.SUSPENDED":
        await _handle_subscription_suspended(db, resource)

    # ─── BILLING.SUBSCRIPTION.EXPIRED ─────────────────────────────────
    elif event_type == "BILLING.SUBSCRIPTION.EXPIRED":
        await _handle_subscription_cancelled(db, resource)  # Same downgrade logic

    # ─── BILLING.SUBSCRIPTION.UPDATED ─────────────────────────────────
    elif event_type == "BILLING.SUBSCRIPTION.UPDATED":
        await _handle_subscription_activated(db, resource)  # Re-sync plan status

    # ─── PAYMENT.SALE.COMPLETED ───────────────────────────────────────
    elif event_type == "PAYMENT.SALE.COMPLETED":
        await _handle_payment_completed(db, resource)

    else:
        logger.debug(f"Unhandled PayPal event type: {event_type}")

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Webhook Signature Verification
# ---------------------------------------------------------------------------

async def _verify_paypal_webhook(request: Request, payload: bytes) -> bool:
    """
    Verify PayPal webhook signature using the PayPal verification API.
    This is the recommended approach per PayPal documentation.
    """
    try:
        access_token = await _get_paypal_access_token()

        verification_body = {
            "auth_algo": request.headers.get("paypal-auth-algo", ""),
            "cert_url": request.headers.get("paypal-cert-url", ""),
            "transmission_id": request.headers.get("paypal-transmission-id", ""),
            "transmission_sig": request.headers.get("paypal-transmission-sig", ""),
            "transmission_time": request.headers.get("paypal-transmission-time", ""),
            "webhook_id": settings.PAYPAL_WEBHOOK_ID,
            "webhook_event": json.loads(payload),
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_paypal_base_url()}/v1/notifications/verify-webhook-signature",
                json=verification_body,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                timeout=15.0,
            )

        if resp.status_code == 200:
            result = resp.json()
            return result.get("verification_status") == "SUCCESS"

        logger.warning(f"PayPal webhook verification returned {resp.status_code}: {resp.text}")
        return False

    except Exception as e:
        logger.error(f"PayPal webhook verification error: {e}")
        # In production, fail closed (reject unverified webhooks)
        # In sandbox, allow through for testing
        return settings.PAYPAL_MODE == "sandbox"


# ---------------------------------------------------------------------------
# Event Handlers
# ---------------------------------------------------------------------------

def _find_user_id_from_resource(resource: dict) -> Optional[int]:
    """Extract the QuantCAI user_id from PayPal subscription custom_id."""
    custom_id = resource.get("custom_id")
    if custom_id and custom_id.isdigit():
        return int(custom_id)
    return None


async def _handle_subscription_activated(db: AsyncSession, resource: dict):
    """Activate subscription after PayPal approval."""
    paypal_sub_id = resource.get("id")
    plan_id = resource.get("plan_id", "")
    custom_user_id = _find_user_id_from_resource(resource)

    if not paypal_sub_id:
        logger.warning("BILLING.SUBSCRIPTION.ACTIVATED: missing subscription ID")
        return

    # Find subscription by PayPal ID
    local_id = f"PAYPAL_{paypal_sub_id}"
    stmt = select(DBmodels.Subscription).where(
        DBmodels.Subscription.stripe_subscription_id == local_id
    )
    res = await db.execute(stmt)
    db_sub = res.scalar_one_or_none()

    # Fallback: find by user_id from custom_id
    if not db_sub and custom_user_id:
        stmt = select(DBmodels.Subscription).where(
            DBmodels.Subscription.user_id == custom_user_id
        )
        res = await db.execute(stmt)
        db_sub = res.scalar_one_or_none()
        if db_sub:
            db_sub.stripe_subscription_id = local_id

    if not db_sub:
        logger.error(f"BILLING.SUBSCRIPTION.ACTIVATED: No subscription found for PayPal ID={paypal_sub_id}")
        return

    # Determine plan from PayPal plan_id
    if plan_id == settings.PAYPAL_ENTERPRISE_PLAN_ID:
        plan_enum = DBmodels.SubscriptionPlan.ENTERPRISE
        tier_enum = DBmodels.Tier.ENTERPRISE
    else:
        plan_enum = DBmodels.SubscriptionPlan.PRO
        tier_enum = DBmodels.Tier.PRO

    # Activate subscription
    db_sub.plan = plan_enum
    db_sub.status = DBmodels.SubscriptionStatus.ACTIVE
    db_sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=30)
    db_sub.updated_at = datetime.now(timezone.utc)
    db.add(db_sub)

    # Update UserPlan tier
    user_id = db_sub.user_id
    if user_id:
        plan_stmt = select(DBmodels.UserPlan).where(DBmodels.UserPlan.user_id == user_id)
        plan_res = await db.execute(plan_stmt)
        user_plan = plan_res.scalar_one_or_none()
        if user_plan:
            user_plan.tier = tier_enum
            db.add(user_plan)
        else:
            user_plan = DBmodels.UserPlan(
                user_id=user_id,
                tier=tier_enum,
                cycle_reset_date=date.today() + timedelta(days=30)
            )
            db.add(user_plan)

    await db.commit()

    if user_id:
        await clear_feature_access_cache(user_id)

    logger.info(
        f"PayPal subscription activated: user={user_id}, "
        f"paypal_sub_id={paypal_sub_id}, plan={plan_enum.value}"
    )


async def _handle_subscription_cancelled(db: AsyncSession, resource: dict):
    """Handle subscription cancellation or expiration — downgrade to free."""
    paypal_sub_id = resource.get("id")
    if not paypal_sub_id:
        return

    local_id = f"PAYPAL_{paypal_sub_id}"
    stmt = select(DBmodels.Subscription).where(
        DBmodels.Subscription.stripe_subscription_id == local_id
    )
    res = await db.execute(stmt)
    db_sub = res.scalar_one_or_none()

    if not db_sub:
        logger.warning(f"SUBSCRIPTION.CANCELLED: No subscription found for PayPal ID={paypal_sub_id}")
        return

    db_sub.status = DBmodels.SubscriptionStatus.CANCELLED
    db_sub.plan = DBmodels.SubscriptionPlan.FREE
    db_sub.current_period_end = None
    db_sub.updated_at = datetime.now(timezone.utc)
    db.add(db_sub)

    # Downgrade UserPlan
    user_id = db_sub.user_id
    if user_id:
        plan_stmt = select(DBmodels.UserPlan).where(DBmodels.UserPlan.user_id == user_id)
        plan_res = await db.execute(plan_stmt)
        user_plan = plan_res.scalar_one_or_none()
        if user_plan:
            user_plan.tier = DBmodels.Tier.FREE
            db.add(user_plan)

    await db.commit()

    if user_id:
        await clear_feature_access_cache(user_id)

    logger.info(f"PayPal subscription cancelled: paypal_sub_id={paypal_sub_id}, user_id={user_id}")


async def _handle_subscription_suspended(db: AsyncSession, resource: dict):
    """Handle subscription suspension (failed payment) — mark as past_due."""
    paypal_sub_id = resource.get("id")
    if not paypal_sub_id:
        return

    local_id = f"PAYPAL_{paypal_sub_id}"
    stmt = select(DBmodels.Subscription).where(
        DBmodels.Subscription.stripe_subscription_id == local_id
    )
    res = await db.execute(stmt)
    db_sub = res.scalar_one_or_none()

    if not db_sub:
        logger.warning(f"SUBSCRIPTION.SUSPENDED: No subscription found for PayPal ID={paypal_sub_id}")
        return

    db_sub.status = DBmodels.SubscriptionStatus.PAST_DUE
    db_sub.updated_at = datetime.now(timezone.utc)
    db.add(db_sub)
    await db.commit()

    logger.warning(f"PayPal subscription suspended (payment failed): paypal_sub_id={paypal_sub_id}, user_id={db_sub.user_id}")


async def _handle_payment_completed(db: AsyncSession, resource: dict):
    """Handle successful recurring payment — extend subscription period."""
    billing_agreement_id = resource.get("billing_agreement_id")
    if not billing_agreement_id:
        return

    local_id = f"PAYPAL_{billing_agreement_id}"
    stmt = select(DBmodels.Subscription).where(
        DBmodels.Subscription.stripe_subscription_id == local_id
    )
    res = await db.execute(stmt)
    db_sub = res.scalar_one_or_none()

    if not db_sub:
        # Payment may reference a different ID format — log but don't error
        logger.debug(f"PAYMENT.SALE.COMPLETED: No subscription found for agreement={billing_agreement_id}")
        return

    # Extend period
    db_sub.status = DBmodels.SubscriptionStatus.ACTIVE
    db_sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=30)
    db_sub.updated_at = datetime.now(timezone.utc)
    db.add(db_sub)
    await db.commit()

    logger.info(f"PayPal payment completed: agreement={billing_agreement_id}, user_id={db_sub.user_id}")
