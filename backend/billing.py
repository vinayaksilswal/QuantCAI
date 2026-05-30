import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import stripe

import models as DBmodels
from core.database import async_session_factory, get_db
from security import redis_client, get_subscription_plan, get_current_user
from core.config import settings

logger = logging.getLogger("quantcai.billing")

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
STRIPE_API_KEY = settings.STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET = settings.STRIPE_WEBHOOK_SECRET
STRIPE_PRO_PRICE_ID = settings.STRIPE_PRO_PRICE_ID or "price_pro_default"
STRIPE_ENTERPRISE_PRICE_ID = settings.STRIPE_ENTERPRISE_PRICE_ID or "price_enterprise_default"

# Default success/cancel URLs derived from frontend origin
FRONTEND_URL = settings.FRONTEND_URL.split(",")[0]

# Initialize Stripe API key
stripe.api_key = STRIPE_API_KEY

# Map Stripe Price IDs to SubscriptionPlan values
PRICE_TO_PLAN = {
    STRIPE_PRO_PRICE_ID: DBmodels.SubscriptionPlan.PRO,
    STRIPE_ENTERPRISE_PRICE_ID: DBmodels.SubscriptionPlan.ENTERPRISE,
}

# -----------------------------------------------------------------------------
# FastAPI Router Setup
# -----------------------------------------------------------------------------
router = APIRouter(prefix="/billing", tags=["Billing & Subscriptions"])

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
def map_price_to_plan(price_id: Optional[str]) -> DBmodels.SubscriptionPlan:
    """Map Stripe Price ID to SubscriptionPlan enum."""
    if not price_id:
        return DBmodels.SubscriptionPlan.FREE
    return PRICE_TO_PLAN.get(price_id, DBmodels.SubscriptionPlan.FREE)

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

# -----------------------------------------------------------------------------
# Core Billing Services
# -----------------------------------------------------------------------------
async def create_checkout_session(user: DBmodels.User, plan: str, db: AsyncSession) -> str:
    """
    Create or retrieve a Stripe customer ID and return a Checkout Session URL.
    """
    if not STRIPE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe API key is not configured."
        )

    # 1. Retrieve or create Stripe customer
    customer_id = user.stripe_customer_id
    if not customer_id:
        try:
            # First, check Stripe if customer already exists under this email
            existing = stripe.Customer.list(email=user.email, limit=1)
            if existing.data:
                customer_id = existing.data[0].id
            else:
                customer = stripe.Customer.create(
                    email=user.email,
                    name=user.name,
                    metadata={"user_id": str(user.id)}
                )
                customer_id = customer.id
            
            # Persist customer ID to user record
            user.stripe_customer_id = customer_id
            db.add(user)
            await db.commit()
            await db.refresh(user)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Stripe Customer Portal initialization failed: {e.user_message}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in customer lookup/create: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while saving Stripe customer metadata."
            )

    # 2. Map plan to Price ID
    plan_lower = plan.lower()
    if plan_lower == "pro":
        price_id = STRIPE_PRO_PRICE_ID
    elif plan_lower == "enterprise":
        price_id = STRIPE_ENTERPRISE_PRICE_ID
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan selection: {plan}. Must be 'pro' or 'enterprise'."
        )

    # 3. Create Checkout Session
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"{FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/billing/cancel",
            metadata={
                "user_id": str(user.id),
                "plan": plan_lower
            }
        )
        return session.url
    except stripe.error.StripeError as e:
        logger.error(f"Stripe checkout session creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe integration error: {e.user_message}"
        )

async def create_customer_portal_session(user: DBmodels.User) -> str:
    """
    Allows users to self-manage billing, cancel, update card, etc.
    """
    if not STRIPE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe API key is not configured."
        )

    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No billing record found. Please complete a checkout first."
        )

    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=f"{FRONTEND_URL}/billing"
        )
        return portal_session.url
    except stripe.error.StripeError as e:
        logger.error(f"Stripe customer portal session creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe Portal error: {e.user_message}"
        )

async def check_feature_access(
    user: DBmodels.User,
    feature: str,
    db: Optional[AsyncSession] = None
) -> bool:
    """
    Check if a user has access to a specific feature based on their active plan.
    Feature options: "ai_tutor_pro", "pqc_scan", "api_access", "cbom_export"
    
    Caches the access result in Redis for 60 seconds.
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
        await redis_client.setex(cache_key, 60, "true" if has_access else "false")
    except Exception as e:
        logger.error(f"Redis cache write failed: {e}", exc_info=True)

    return has_access

# -----------------------------------------------------------------------------
# Webhook Handler and Asynchronous Background Processing
# -----------------------------------------------------------------------------
@router.post("/webhook")
async def stripe_webhook_handler(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Verifies Stripe webhook signature and dispatches event handling asynchronously.
    """
    if not STRIPE_WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET is not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret is not configured on the server."
        )

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="stripe-signature header is missing"
        )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )

    # Process asynchronously to avoid Stripe gateway timeout retries
    background_tasks.add_task(process_webhook_event_async, event)
    return {"status": "event_received"}


async def process_webhook_event_async(event: Dict[str, Any]):
    """
    Asynchronous event router for verified webhook payloads.
    """
    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})
    logger.info(f"Processing Stripe Webhook event: {event_type} (ID: {event.get('id')})")

    try:
        if event_type == "checkout.session.completed":
            await handle_checkout_session_completed(data_object)
        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(data_object)
        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(data_object)
        elif event_type == "invoice.payment_failed":
            await handle_invoice_payment_failed(data_object)
        else:
            logger.debug(f"Ignored unhandled Stripe event: {event_type}")
    except Exception as e:
        logger.error(f"Fatal error executing async task for event {event_type}: {e}", exc_info=True)


async def handle_checkout_session_completed(session: Dict[str, Any]):
    """
    Handle checkout.session.completed:
    - Associate customer and subscription with user.
    - Set user's stripe_customer_id.
    - Set subscription status to active and store plan/expiration.
    """
    customer_id = session.get("customer")
    sub_id = session.get("subscription")
    metadata = session.get("metadata", {})
    user_id_str = metadata.get("user_id")
    plan_str = metadata.get("plan")

    if not sub_id:
        logger.warning("checkout.session.completed missing subscription ID.")
        return

    # Retrieve full subscription object to fetch current period end date
    try:
        stripe_sub = stripe.Subscription.retrieve(sub_id)
        current_period_end_ts = stripe_sub.current_period_end
        current_period_end = datetime.fromtimestamp(current_period_end_ts, tz=timezone.utc)
        price_id = stripe_sub.get("items", {}).get("data", [{}])[0].get("price", {}).get("id")
        plan = map_price_to_plan(price_id) or map_string_to_plan(plan_str)
    except Exception as e:
        logger.error(f"Failed to fetch subscription details from Stripe for {sub_id}: {e}", exc_info=True)
        # Default fallback parameters if Stripe API fails
        current_period_end = datetime.fromtimestamp(datetime.now().timestamp() + 30 * 24 * 3600, tz=timezone.utc)
        plan = map_string_to_plan(plan_str)

    async with async_session_factory() as db:
        # Resolve user
        user_id = int(user_id_str) if user_id_str else None
        if not user_id and customer_id:
            stmt = select(DBmodels.User).where(DBmodels.User.stripe_customer_id == customer_id)
            res = await db.execute(stmt)
            user = res.scalar_one_or_none()
            if user:
                user_id = user.id

        if not user_id:
            logger.error(f"Unable to match Stripe customer {customer_id} to a QuantCAI user.")
            return

        # 1. Update user stripe details
        stmt_user = select(DBmodels.User).where(DBmodels.User.id == user_id)
        res_user = await db.execute(stmt_user)
        user = res_user.scalar_one_or_none()
        if user:
            user.stripe_customer_id = customer_id
            db.add(user)

        # 2. Update subscription record
        stmt_sub = select(DBmodels.Subscription).where(
            (DBmodels.Subscription.stripe_subscription_id == sub_id) |
            (DBmodels.Subscription.user_id == user_id)
        )
        res_sub = await db.execute(stmt_sub)
        db_sub = res_sub.scalars().first()

        if db_sub:
            db_sub.stripe_subscription_id = sub_id
            db_sub.status = DBmodels.SubscriptionStatus.ACTIVE
            db_sub.plan = plan
            db_sub.current_period_end = current_period_end
            db_sub.updated_at = datetime.now(timezone.utc)
            db.add(db_sub)
        else:
            db_sub = DBmodels.Subscription(
                user_id=user_id,
                stripe_subscription_id=sub_id,
                plan=plan,
                status=DBmodels.SubscriptionStatus.ACTIVE,
                current_period_end=current_period_end
            )
            db.add(db_sub)

        await db.commit()
        await clear_feature_access_cache(user_id)
        logger.info(f"Successfully processed active subscription {sub_id} for user {user_id}")


async def handle_subscription_updated(stripe_sub: Dict[str, Any]):
    """
    Handle customer.subscription.updated:
    - Update plan, period_end and status in database.
    """
    sub_id = stripe_sub.get("id")
    customer_id = stripe_sub.get("customer")
    status_str = stripe_sub.get("status")
    current_period_end_ts = stripe_sub.get("current_period_end")
    current_period_end = datetime.fromtimestamp(current_period_end_ts, tz=timezone.utc) if current_period_end_ts else None

    price_id = stripe_sub.get("items", {}).get("data", [{}])[0].get("price", {}).get("id")
    plan = map_price_to_plan(price_id)

    status_map = {
        "active": DBmodels.SubscriptionStatus.ACTIVE,
        "past_due": DBmodels.SubscriptionStatus.PAST_DUE,
        "canceled": DBmodels.SubscriptionStatus.CANCELLED,
        "unpaid": DBmodels.SubscriptionStatus.PAST_DUE,
        "trialing": DBmodels.SubscriptionStatus.TRIALING,
    }
    db_status = status_map.get(status_str, DBmodels.SubscriptionStatus.CANCELLED)

    async with async_session_factory() as db:
        stmt_sub = select(DBmodels.Subscription).where(DBmodels.Subscription.stripe_subscription_id == sub_id)
        res_sub = await db.execute(stmt_sub)
        db_sub = res_sub.scalar_one_or_none()

        user_id = None
        if db_sub:
            db_sub.status = db_status
            db_sub.plan = plan
            db_sub.current_period_end = current_period_end
            db_sub.updated_at = datetime.now(timezone.utc)
            user_id = db_sub.user_id
            db.add(db_sub)
        else:
            # Fallback lookup by customer ID
            stmt_user = select(DBmodels.User).where(DBmodels.User.stripe_customer_id == customer_id)
            res_user = await db.execute(stmt_user)
            user = res_user.scalar_one_or_none()
            if user:
                user_id = user.id
                db_sub = DBmodels.Subscription(
                    user_id=user_id,
                    stripe_subscription_id=sub_id,
                    plan=plan,
                    status=db_status,
                    current_period_end=current_period_end
                )
                db.add(db_sub)

        await db.commit()
        if user_id:
            await clear_feature_access_cache(user_id)
            logger.info(f"Updated subscription {sub_id} for user {user_id} to status: {db_status.value}")


async def handle_subscription_deleted(stripe_sub: Dict[str, Any]):
    """
    Handle customer.subscription.deleted:
    - Set status to cancelled, downgrade subscription to free.
    """
    sub_id = stripe_sub.get("id")
    customer_id = stripe_sub.get("customer")

    async with async_session_factory() as db:
        stmt_sub = select(DBmodels.Subscription).where(DBmodels.Subscription.stripe_subscription_id == sub_id)
        res_sub = await db.execute(stmt_sub)
        db_sub = res_sub.scalar_one_or_none()

        user_id = None
        if db_sub:
            db_sub.status = DBmodels.SubscriptionStatus.CANCELLED
            db_sub.plan = DBmodels.SubscriptionPlan.FREE
            db_sub.current_period_end = None
            db_sub.updated_at = datetime.now(timezone.utc)
            user_id = db_sub.user_id
            db.add(db_sub)
        else:
            stmt_user = select(DBmodels.User).where(DBmodels.User.stripe_customer_id == customer_id)
            res_user = await db.execute(stmt_user)
            user = res_user.scalar_one_or_none()
            if user:
                user_id = user.id
                db_sub = DBmodels.Subscription(
                    user_id=user_id,
                    stripe_subscription_id=sub_id,
                    plan=DBmodels.SubscriptionPlan.FREE,
                    status=DBmodels.SubscriptionStatus.CANCELLED,
                    current_period_end=None
                )
                db.add(db_sub)

        await db.commit()
        if user_id:
            await clear_feature_access_cache(user_id)
            logger.info(f"Cancelled subscription {sub_id} for user {user_id}; downgraded to free plan")


async def handle_invoice_payment_failed(invoice: Dict[str, Any]):
    """
    Handle invoice.payment_failed:
    - Set status to past_due.
    - Trigger email alert.
    """
    sub_id = invoice.get("subscription")
    customer_id = invoice.get("customer")
    invoice_id = invoice.get("id")

    async with async_session_factory() as db:
        user_id = None
        user_email = None

        if sub_id:
            stmt_sub = select(DBmodels.Subscription).where(DBmodels.Subscription.stripe_subscription_id == sub_id)
            res_sub = await db.execute(stmt_sub)
            db_sub = res_sub.scalar_one_or_none()
            if db_sub:
                db_sub.status = DBmodels.SubscriptionStatus.PAST_DUE
                db_sub.updated_at = datetime.now(timezone.utc)
                user_id = db_sub.user_id
                db.add(db_sub)

        # Fallback resolves to ensure we get user ID and email
        if not user_id and customer_id:
            stmt_user = select(DBmodels.User).where(DBmodels.User.stripe_customer_id == customer_id)
            res_user = await db.execute(stmt_user)
            user = res_user.scalar_one_or_none()
            if user:
                user_id = user.id
                user_email = user.email

        if user_id and not user_email:
            stmt_user = select(DBmodels.User).where(DBmodels.User.id == user_id)
            res_user = await db.execute(stmt_user)
            user = res_user.scalar_one_or_none()
            if user:
                user_email = user.email

        await db.commit()

        if user_id:
            await clear_feature_access_cache(user_id)

        if user_email:
            await send_payment_failed_email(user_email, invoice_id)
        else:
            logger.warning(f"Could not resolve email alert recipient for customer_id: {customer_id}")


async def send_payment_failed_email(email: str, invoice_id: Optional[str]):
    """
    Logs and triggers a mock email alert for invoice payment failures.
    """
    logger.error(
        f"EMAIL ALERT: Invoice payment failed for customer email {email}. "
        f"Invoice ID: {invoice_id}. Account marked as past_due."
    )

@router.post("/checkout")
async def billing_checkout(
    plan: str = "pro",
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a Stripe checkout session URL for the selected plan and return it.
    """
    try:
        url = await create_checkout_session(current_user, plan, db)
        return {"url": url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/portal")
async def billing_portal(
    current_user: DBmodels.User = Depends(get_current_user)
):
    """
    Generate a Stripe billing customer portal URL and return it.
    """
    try:
        url = await create_customer_portal_session(current_user)
        return {"url": url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating portal session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

