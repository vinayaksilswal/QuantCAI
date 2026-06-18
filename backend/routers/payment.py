import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models as DBmodels
from core.database import get_db
from core.config import settings
from core.auth import get_current_user
from billing import clear_feature_access_cache

router = APIRouter(tags=["Payments"])
logger = logging.getLogger("quantcai.payments")

@router.post("/api/payment/warriorplus/ipn")
async def warriorplus_ipn_handler(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    WarriorPlus IPN webhook handler.
    
    DEPRECATED: This handler is in a 90-day sunset period.
    New subscriptions should use the Stripe billing integration at /api/billing/checkout.
    This endpoint will be removed after the deprecation window closes.
    
    Validates security key, creates/updates user account, and activates/cancels Pro plan.
    """
    logger.warning(
        "DEPRECATION: WarriorPlus IPN handler invoked. "
        "This endpoint is deprecated and will be removed. "
        "Migrate subscribers to Stripe billing at /api/billing/checkout."
    )
    form_data = await request.form()
    logger.info(f"Received WarriorPlus IPN notification: {dict(form_data)}")

    # 1. Validate security key
    security_key = form_data.get("WP_SECURITYKEY")
    expected_key = settings.WARRIORPLUS_SECURITY_KEY
    
    if not expected_key:
        logger.error("WARRIORPLUS_SECURITY_KEY is not configured on the server.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="WarriorPlus integration is not configured on the server."
        )
        
    if security_key != expected_key:
        logger.warning(f"Invalid security key received in WarriorPlus IPN: {security_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid security key."
        )

    # 2. Extract parameters
    action = form_data.get("WP_ACTION")
    email = form_data.get("WP_BUYER_EMAIL")
    name = form_data.get("WP_BUYER_NAME", "WarriorPlus Customer")
    sale_id = form_data.get("WP_SALEID")
    payment_status = form_data.get("WP_PAYMENT_STATUS")

    if not email:
        logger.error("Missing buyer email in WarriorPlus IPN notification.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing buyer email."
        )

    # Convert email to lowercase for consistency
    email = email.lower().strip()

    if action == "sale":
        # Ensure payment is completed
        if payment_status != "Completed":
            logger.warning(f"WarriorPlus sale notification status is '{payment_status}', not 'Completed'. Ignoring.")
            return {"status": "ignored", "reason": f"Payment status is {payment_status}"}

        # Query user
        stmt_user = select(DBmodels.User).where(DBmodels.User.email == email)
        res_user = await db.execute(stmt_user)
        user = res_user.scalar_one_or_none()

        temp_password = None
        if not user:
            # Create a new user with random password
            import secrets
            from core.auth import hash_password
            temp_password = sale_id if sale_id else secrets.token_urlsafe(12)
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
            logger.info(f"Created new user via WarriorPlus purchase: {email} (ID: {user.id})")
        else:
            logger.info(f"Existing user found for WarriorPlus purchase: {email} (ID: {user.id})")

        # Create or update subscription to PRO
        stmt_sub = select(DBmodels.Subscription).where(DBmodels.Subscription.user_id == user.id)
        res_sub = await db.execute(stmt_sub)
        db_sub = res_sub.scalars().first()

        period_end = datetime.now(timezone.utc) + timedelta(days=30)
        sub_id = f"warriorplus_{sale_id}" if sale_id else None

        if db_sub:
            db_sub.status = DBmodels.SubscriptionStatus.ACTIVE
            db_sub.plan = DBmodels.SubscriptionPlan.PRO
            if sub_id:
                db_sub.stripe_subscription_id = sub_id
            db_sub.current_period_end = period_end
            db_sub.updated_at = datetime.now(timezone.utc)
            db.add(db_sub)
        else:
            db_sub = DBmodels.Subscription(
                user_id=user.id,
                stripe_subscription_id=sub_id,
                plan=DBmodels.SubscriptionPlan.PRO,
                status=DBmodels.SubscriptionStatus.ACTIVE,
                current_period_end=period_end
            )
            db.add(db_sub)

        await db.commit()

        # Clear feature access Redis cache
        await clear_feature_access_cache(user.id)

        # Trigger mock welcome email if a new account was created
        if temp_password:
            logger.info(
                f"EMAIL ALERT: Welcome to QuantCAI! Your account has been created via WarriorPlus. "
                f"Email: {email}, Temporary Password: {temp_password}. Log in at {settings.FRONTEND_URL}/login"
            )

        logger.info(f"Activated Pro subscription for user {email} via WarriorPlus sale {sale_id}")
        return {"status": "success", "message": "Subscription activated successfully"}

    elif action in ("refund", "dispute", "cancel") or (action and "cancel" in action.lower()):
        # Downgrade user's subscription to FREE
        stmt_user = select(DBmodels.User).where(DBmodels.User.email == email)
        res_user = await db.execute(stmt_user)
        user = res_user.scalar_one_or_none()

        if not user:
            logger.warning(f"Received WarriorPlus unsubscribe/refund action '{action}' for non-existent user: {email}")
            return {"status": "ignored", "reason": "User not found"}

        stmt_sub = select(DBmodels.Subscription).where(DBmodels.Subscription.user_id == user.id)
        res_sub = await db.execute(stmt_sub)
        db_sub = res_sub.scalars().first()

        if db_sub:
            db_sub.status = DBmodels.SubscriptionStatus.CANCELLED
            db_sub.plan = DBmodels.SubscriptionPlan.FREE
            db_sub.current_period_end = None
            db_sub.updated_at = datetime.now(timezone.utc)
            db.add(db_sub)
            await db.commit()
            await clear_feature_access_cache(user.id)
            logger.info(f"Cancelled subscription for user {email} (ID: {user.id}) via WarriorPlus action {action}")
            return {"status": "success", "message": "Subscription cancelled successfully"}
        else:
            logger.warning(f"No active subscription found to cancel for user {email} (ID: {user.id})")
            return {"status": "ignored", "reason": "No subscription found"}

    else:
        logger.warning(f"Unsupported WarriorPlus action received: {action}")
        return {"status": "ignored", "reason": f"Action {action} is not supported"}

