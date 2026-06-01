import time
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import razorpay
from razorpay.errors import SignatureVerificationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models as DBmodels
from core.database import get_db
from core.config import settings
from core.auth import get_current_user
from billing import clear_feature_access_cache

router = APIRouter(tags=["Razorpay Payments"])
logger = logging.getLogger("quantcai.payments")

class CreateOrderRequest(BaseModel):
    amount: float  # Amount in USD

class VerifyPaymentRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str

@router.post("/create-order")
async def create_order(
    request: CreateOrderRequest,
    current_user: DBmodels.User = Depends(get_current_user)
):
    """
    Creates a Razorpay order with currency='USD' and amount in cents.
    """
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        logger.error("Razorpay API key or secret not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Razorpay is not configured on the backend."
        )

    try:
        # Initialize Razorpay Client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Convert USD to cents (multiply by 100) and round to avoid floating point inaccuracies
        amount_in_cents = int(round(request.amount * 100))

        # Order creation details
        order_data = {
            "amount": amount_in_cents,
            "currency": "USD",
            "receipt": f"receipt_order_{current_user.id}_{int(time.time())}",
            "notes": {
                "user_id": str(current_user.id),
                "user_email": current_user.email
            }
        }

        # Call Razorpay SDK to create the order
        order = client.order.create(data=order_data)
        logger.info(f"Successfully created Razorpay order {order.get('id')} for user {current_user.email}")
        return order

    except Exception as e:
        logger.error(f"Failed to create Razorpay order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order creation failed: {str(e)}"
        )

@router.post("/verify-payment")
async def verify_payment(
    request: VerifyPaymentRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifies a Razorpay payment signature. If successful, activates the user's Pro plan in the DB.
    """
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        logger.error("Razorpay API key or secret not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Razorpay is not configured on the backend."
        )

    try:
        # Initialize Razorpay Client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Validate signature
        params_dict = {
            "razorpay_order_id": request.razorpay_order_id,
            "razorpay_payment_id": request.razorpay_payment_id,
            "razorpay_signature": request.razorpay_signature
        }

        client.utility.verify_payment_signature(params_dict)
        logger.info(f"Razorpay signature verified successfully for order {request.razorpay_order_id}")

        # Update user subscription in database to Pro
        stmt_sub = select(DBmodels.Subscription).where(
            DBmodels.Subscription.user_id == current_user.id
        )
        res_sub = await db.execute(stmt_sub)
        db_sub = res_sub.scalars().first()

        # Pro subscription duration: 30 days from now
        period_end = datetime.now(timezone.utc) + timedelta(days=30)

        if db_sub:
            db_sub.status = DBmodels.SubscriptionStatus.ACTIVE
            db_sub.plan = DBmodels.SubscriptionPlan.PRO
            db_sub.stripe_subscription_id = f"razorpay_{request.razorpay_order_id}"
            db_sub.current_period_end = period_end
            db_sub.updated_at = datetime.now(timezone.utc)
            db.add(db_sub)
        else:
            db_sub = DBmodels.Subscription(
                user_id=current_user.id,
                stripe_subscription_id=f"razorpay_{request.razorpay_order_id}",
                plan=DBmodels.SubscriptionPlan.PRO,
                status=DBmodels.SubscriptionStatus.ACTIVE,
                current_period_end=period_end
            )
            db.add(db_sub)

        await db.commit()

        # Clear feature access caching in Redis
        await clear_feature_access_cache(current_user.id)
        logger.info(f"Upgraded user {current_user.email} (ID: {current_user.id}) to Pro subscription plan.")

        return {
            "status": "success",
            "message": "Payment verified successfully, plan upgraded to Pro"
        }

    except SignatureVerificationError as e:
        logger.warning(f"Razorpay payment signature mismatch for order {request.razorpay_order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed: Signature mismatch"
        )
    except Exception as e:
        logger.error(f"Error occurred during Razorpay payment verification: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )
