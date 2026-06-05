import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
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
    amount: int  # Amount in paise (e.g., 240000 = ₹2,400)
    currency: str = "INR"
    receipt: Optional[str] = None

class VerifyPaymentRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str

@router.post("/api/create-order")
async def create_order(
    request: CreateOrderRequest,
    current_user: DBmodels.User = Depends(get_current_user)
):
    """
    Creates a Razorpay order for the given amount and currency.
    Returns the order_id to be used by the frontend Razorpay checkout widget.
    """
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        logger.error("Razorpay API key or secret not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment gateway is not configured. Please contact support."
        )

    # Validate amount >= 100 paise (₹1)
    if request.amount < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be at least ₹1 (100 paise)."
        )

    try:
        # Initialize Razorpay Client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Order creation details
        order_data = {
            "amount": request.amount,
            "currency": request.currency,
            "receipt": request.receipt or f"receipt_order_{current_user.id}_{int(datetime.now(timezone.utc).timestamp())}",
            "notes": {
                "user_id": str(current_user.id),
                "user_email": current_user.email
            }
        }

        # Call Razorpay SDK to create the order
        order = client.order.create(data=order_data)
        logger.info(f"Created Razorpay order {order.get('id')} for user {current_user.email} (amount: {request.amount} paise)")
        
        return {
            "order_id": order.get("id"),
            "amount": order.get("amount"),
            "currency": order.get("currency"),
        }

    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay bad request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to create Razorpay order: {str(e)}", exc_info=True)
        err_msg = str(e).lower()

        if "auth" in err_msg or "unauthorized" in err_msg or "401" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Payment gateway authentication failed. Please contact support."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment order. Please try again later."
        )

@router.post("/api/verify-payment")
async def verify_payment(
    request: VerifyPaymentRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifies a Razorpay payment signature. If valid, activates the user's Pro plan.
    This is a critical security endpoint — never skip signature verification.
    """
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        logger.error("Razorpay API key or secret not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment gateway is not configured. Please contact support."
        )

    # All fields are required (enforced by Pydantic model)
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
        logger.info(f"Razorpay signature verified for order {request.razorpay_order_id}, payment {request.razorpay_payment_id}")

    except SignatureVerificationError as e:
        logger.warning(f"Payment signature mismatch for order {request.razorpay_order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed: Invalid signature. Please contact support if you were charged."
        )
    except Exception as e:
        logger.error(f"Error during payment verification: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment verification failed. Please contact support if you were charged."
        )

    # Signature verified — activate Pro subscription
    try:
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
            db_sub.stripe_subscription_id = f"razorpay_{request.razorpay_payment_id}"
            db_sub.current_period_end = period_end
            db_sub.updated_at = datetime.now(timezone.utc)
            db.add(db_sub)
        else:
            db_sub = DBmodels.Subscription(
                user_id=current_user.id,
                stripe_subscription_id=f"razorpay_{request.razorpay_payment_id}",
                plan=DBmodels.SubscriptionPlan.PRO,
                status=DBmodels.SubscriptionStatus.ACTIVE,
                current_period_end=period_end
            )
            db.add(db_sub)

        await db.commit()

        # Clear feature access caching in Redis
        await clear_feature_access_cache(current_user.id)
        logger.info(f"Activated Pro subscription for user {current_user.email} (ID: {current_user.id}), payment: {request.razorpay_payment_id}")

        return {
            "status": "success",
            "message": "Payment verified successfully. Your plan has been upgraded to Pro!"
        }
    except Exception as e:
        logger.error(f"Database error during subscription activation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment was verified but subscription activation failed. Please contact support."
        )
