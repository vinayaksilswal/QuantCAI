"""
QuantCAI — WarriorPlus IPN Handler (PRIMARY SUBSCRIPTION GATEWAY)
==================================================================
Production-ready handler for WarriorPlus Instant Payment Notifications.
Handles subscription activation (Pro/Enterprise) and cancellation.

Security features:
  - Security key validation
  - Redis-based idempotency (prevents duplicate processing)
  - SELECT ... FOR UPDATE (prevents race conditions)
  - No plaintext secrets in logs
  - Structured logging with correlation IDs (sale_id)
"""

import hmac
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models as DBmodels
from core.database import get_db
from core.config import settings
from billing import clear_feature_access_cache
from security import redis_client
from tier_limits import sync_user_plan_tier
from services.meta_capi import send_purchase_event_to_meta

router = APIRouter(tags=["Payments"])
logger = logging.getLogger("quantcai.payments")

# IPN idempotency TTL: 24 hours (WarriorPlus may retry IPNs)
IPN_IDEMPOTENCY_TTL = 86400


def _determine_tier_from_product(form_data: dict) -> DBmodels.SubscriptionPlan:
    """
    Determine the subscription tier based on WarriorPlus product/offer ID.
    Falls back to PRO if no product mapping is configured.
    """
    # WarriorPlus sends the product/offer identifier as WP_ITEM_NUMBER. Reading
    # only WP_ITEM_ID/WP_OFFER_ID meant product_id was always empty on real
    # IPNs — harmless while this function defaulted to PRO, but the moment that
    # default became FREE it would have downgraded every genuine purchase.
    # Checked first, with the other spellings kept as fallbacks.
    product_id = (
        form_data.get("WP_ITEM_NUMBER", "")
        or form_data.get("WP_ITEM_ID", "")
        or form_data.get("WP_OFFER_ID", "")
    )

    if settings.WARRIORPLUS_ENTERPRISE_PRODUCT_ID and product_id == settings.WARRIORPLUS_ENTERPRISE_PRODUCT_ID:
        return DBmodels.SubscriptionPlan.ENTERPRISE

    if settings.WARRIORPLUS_PRO_PRODUCT_ID and product_id == settings.WARRIORPLUS_PRO_PRODUCT_ID:
        return DBmodels.SubscriptionPlan.PRO

    # No mapping matched.
    #
    # This used to grant PRO unconditionally. Both product-ID settings default
    # to "", so on an unconfigured deployment EVERY sale granted Pro — and once
    # configured, any *other* product sold through the same WarriorPlus account
    # (a tripwire, an ebook, an unrelated offer) would also grant a full Pro
    # subscription. Granting paid entitlements to unrecognised products is a
    # revenue leak, so default to FREE and make the misconfiguration loud.
    if not (settings.WARRIORPLUS_PRO_PRODUCT_ID or settings.WARRIORPLUS_ENTERPRISE_PRODUCT_ID):
        logger.error(
            "No WarriorPlus product IDs configured. Set WARRIORPLUS_PRO_PRODUCT_ID "
            "and WARRIORPLUS_ENTERPRISE_PRODUCT_ID, or paid sales cannot be mapped "
            "to a tier. Granting FREE for product_id=%r.",
            product_id,
        )
    else:
        logger.warning(
            "Unrecognised WarriorPlus product_id=%r — not a configured Pro or "
            "Enterprise offer. Granting FREE.",
            product_id,
        )
    return DBmodels.SubscriptionPlan.FREE


@router.post("/api/payment/warriorplus/ipn")
async def warriorplus_ipn_handler(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    WarriorPlus IPN webhook handler — PRIMARY SUBSCRIPTION GATEWAY.

    Handles:
      - 'sale' action: Create/upgrade subscription (Pro or Enterprise)
      - 'refund'/'dispute'/'cancel': Downgrade subscription to FREE

    Security:
      - Validates WP_SECURITYKEY against configured secret
      - Redis-based idempotency prevents duplicate processing
      - SELECT ... FOR UPDATE prevents race conditions on subscription rows
    """
    form_data = await request.form()
    form_dict = dict(form_data)

    # Extract correlation ID early for all log messages
    sale_id = form_dict.get("WP_SALEID", "unknown")
    action = form_dict.get("WP_ACTION", "unknown")

    # Log incoming IPN (redact security key)
    safe_data = {k: v for k, v in form_dict.items() if k != "WP_SECURITYKEY"}
    logger.info(f"[IPN:{sale_id}] WarriorPlus IPN received: action={action}, data={safe_data}")

    # ── 1. Validate security key ──────────────────────────────────────────
    security_key = form_dict.get("WP_SECURITYKEY")
    expected_key = settings.WARRIORPLUS_SECURITY_KEY

    if not expected_key:
        logger.error(f"[IPN:{sale_id}] WARRIORPLUS_SECURITY_KEY is not configured.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="WarriorPlus integration is not configured on the server."
        )

    # Constant-time comparison: a plain != leaks the shared secret's prefix
    # length through response timing to an attacker able to submit IPNs.
    if not hmac.compare_digest(str(security_key or ""), str(expected_key)):
        logger.warning(f"[IPN:{sale_id}] Invalid security key received")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid security key."
        )

    # ── 2. Idempotency check ──────────────────────────────────────────────
    idempotency_key = f"wp_ipn:{sale_id}:{action}"
    try:
        already_processed = await redis_client.set(
            idempotency_key, "1", nx=True, ex=IPN_IDEMPOTENCY_TTL
        )
        if not already_processed:
            logger.info(f"[IPN:{sale_id}] Duplicate IPN detected, skipping")
            return {"status": "ok", "message": "Event already processed"}
    except Exception as redis_err:
        # If Redis is down, log and continue (fail-open for idempotency)
        logger.warning(f"[IPN:{sale_id}] Redis idempotency check failed: {redis_err}")

    # ── 3. Extract parameters ─────────────────────────────────────────────
    email = form_dict.get("WP_BUYER_EMAIL")
    name = form_dict.get("WP_BUYER_NAME", "WarriorPlus Customer")
    payment_status = form_dict.get("WP_PAYMENT_STATUS")
    custom = form_dict.get("WP_CUSTOM")

    if not email:
        logger.error(f"[IPN:{sale_id}] Missing buyer email")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing buyer email."
        )

    email = email.lower().strip()

    # ── 4. Handle SALE action ─────────────────────────────────────────────
    if action == "sale":
        # WP_ACTION=sale is itself the completed-sale notification, and
        # WP_PAYMENT_STATUS is not present on every sale IPN. Requiring it to
        # equal "Completed" therefore silently dropped legitimate purchases —
        # the buyer is charged and never provisioned, which is the most
        # expensive failure this handler can have.
        #
        # Still refuse any explicitly non-completed status, so a pending,
        # failed or already-refunded payment cannot grant access.
        if payment_status and payment_status != "Completed":
            logger.warning(
                f"[IPN:{sale_id}] Payment status is '{payment_status}', not 'Completed'. Ignoring."
            )
            return {"status": "ignored", "reason": f"Payment status is {payment_status}"}
        if not payment_status:
            logger.info(
                f"[IPN:{sale_id}] No WP_PAYMENT_STATUS on sale IPN; treating the "
                f"sale action as completed."
            )

        # Determine tier from product/offer ID
        target_plan = _determine_tier_from_product(form_dict)

        # Query or create user
        user = None
        if custom:
            try:
                custom_user_id = int(custom)
                stmt_user = select(DBmodels.User).where(DBmodels.User.id == custom_user_id)
                res_user = await db.execute(stmt_user)
                user = res_user.scalar_one_or_none()
                if user:
                    logger.info(f"[IPN:{sale_id}] Found user via WP_CUSTOM ID: {user.id}")
            except ValueError:
                pass

        if not user:
            stmt_user = select(DBmodels.User).where(DBmodels.User.email == email)
            res_user = await db.execute(stmt_user)
            user = res_user.scalar_one_or_none()

        new_account_created = False
        if not user:
            import secrets
            from core.auth import hash_password
            temp_password = sale_id if sale_id and sale_id != "unknown" else secrets.token_urlsafe(16)
            hashed_pw = hash_password(temp_password)
            user = DBmodels.User(
                email=email,
                hashed_password=hashed_pw,
                name=name.strip(),
                role=DBmodels.UserRole.LEARNER,
                is_active=True,
                email_verified=True
            )
            db.add(user)
            await db.flush()  # Populates user.id
            new_account_created = True
            logger.info(f"[IPN:{sale_id}] Created new user: {email} (ID: {user.id})")
        else:
            logger.info(f"[IPN:{sale_id}] Existing user found: {email} (ID: {user.id})")

        # Create or update subscription with row-level locking
        stmt_sub = (
            select(DBmodels.Subscription)
            .where(DBmodels.Subscription.user_id == user.id)
            .with_for_update()  # Prevent race conditions
        )
        res_sub = await db.execute(stmt_sub)
        db_sub = res_sub.scalars().first()

        period_end = datetime.now(timezone.utc) + timedelta(days=settings.SUBSCRIPTION_PERIOD_DAYS)
        sub_id = f"warriorplus_{sale_id}" if sale_id else None

        if db_sub:
            db_sub.status = DBmodels.SubscriptionStatus.ACTIVE
            db_sub.plan = target_plan
            if sub_id:
                db_sub.stripe_subscription_id = sub_id
            db_sub.current_period_end = period_end
            db_sub.updated_at = datetime.now(timezone.utc)
            db.add(db_sub)
        else:
            db_sub = DBmodels.Subscription(
                user_id=user.id,
                stripe_subscription_id=sub_id,
                plan=target_plan,
                status=DBmodels.SubscriptionStatus.ACTIVE,
                current_period_end=period_end
            )
            db.add(db_sub)

        # Propagate the purchase to UserPlan, which is what every entitlement
        # check actually reads. Writing only to Subscription left UserPlan at
        # FREE, so a paying customer received nothing they bought.
        await sync_user_plan_tier(db, user.id, target_plan.value)

        await db.commit()

        # Clear feature access Redis cache
        await clear_feature_access_cache(user.id)

        # Log account creation (WITHOUT plaintext password)
        if new_account_created:
            logger.info(
                f"[IPN:{sale_id}] New account created for {email}. "
                f"User should reset password at {settings.FRONTEND_URL}/login"
            )

        # Trigger Meta CAPI in background
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
        if client_ip and "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()
        user_agent = request.headers.get("User-Agent")
        
        try:
            amount = float(form_dict.get("WP_ITEM_PRICE") or form_dict.get("WP_AMOUNT") or 0.0)
        except ValueError:
            amount = 0.0

        background_tasks.add_task(
            send_purchase_event_to_meta,
            email=email,
            amount=amount,
            currency="USD",
            sale_id=sale_id,
            client_ip=client_ip,
            user_agent=user_agent
        )

        tier_name = target_plan.value if hasattr(target_plan, "value") else str(target_plan)
        logger.info(
            f"[IPN:{sale_id}] Activated {tier_name} subscription for {email} (user_id={user.id})"
        )
        return {"status": "success", "message": f"{tier_name} subscription activated successfully"}

    # ── 5. Handle REFUND/CANCEL/DISPUTE actions ───────────────────────────
    elif action in ("refund", "dispute", "cancel") or (action and "cancel" in action.lower()):
        stmt_user = select(DBmodels.User).where(DBmodels.User.email == email)
        res_user = await db.execute(stmt_user)
        user = res_user.scalar_one_or_none()

        if not user:
            logger.warning(f"[IPN:{sale_id}] {action} for non-existent user: {email}")
            return {"status": "ignored", "reason": "User not found"}

        # Lock subscription row to prevent concurrent modifications
        stmt_sub = (
            select(DBmodels.Subscription)
            .where(DBmodels.Subscription.user_id == user.id)
            .with_for_update()
        )
        res_sub = await db.execute(stmt_sub)
        db_sub = res_sub.scalars().first()

        if db_sub:
            db_sub.status = DBmodels.SubscriptionStatus.CANCELLED
            db_sub.plan = DBmodels.SubscriptionPlan.FREE
            db_sub.current_period_end = None
            db_sub.updated_at = datetime.now(timezone.utc)
            db.add(db_sub)
            # Revoke entitlements too, or a refunded customer keeps paid access.
            await sync_user_plan_tier(db, user.id, DBmodels.SubscriptionPlan.FREE.value)
            await db.commit()
            await clear_feature_access_cache(user.id)
            logger.info(f"[IPN:{sale_id}] Cancelled subscription for {email} (ID: {user.id}) via {action}")
            return {"status": "success", "message": "Subscription cancelled successfully"}
        else:
            logger.warning(f"[IPN:{sale_id}] No subscription found to cancel for {email}")
            return {"status": "ignored", "reason": "No subscription found"}

    # ── 6. Unrecognized action ────────────────────────────────────────────
    else:
        logger.warning(f"[IPN:{sale_id}] Unsupported action: {action}")
        return {"status": "ignored", "reason": f"Action {action} is not supported"}
