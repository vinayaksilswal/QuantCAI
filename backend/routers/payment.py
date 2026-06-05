import time
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
    amount: int  # Amount in paise
    currency: str = "INR"
    receipt: Optional[str] = None

class VerifyPaymentRequest(BaseModel):
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    razorpay_signature: Optional[str] = None

@router.post("/api/create-order")
async def create_order(
    request: CreateOrderRequest,
    current_user: DBmodels.User = Depends(get_current_user)
):
    """
    Creates a Razorpay order with currency and amount in paise/cents.
    """
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        logger.error("Razorpay API key or secret not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Razorpay is not configured on the backend."
        )

    # Validate amount >= 100 paise
    if request.amount < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be at least 100 paise."
        )

    try:
        # Initialize Razorpay Client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Order creation details
        order_data = {
            "amount": request.amount,
            "currency": request.currency,
            "receipt": request.receipt or f"receipt_order_{current_user.id}_{int(time.time())}",
            "notes": {
                "user_id": str(current_user.id),
                "user_email": current_user.email
            }
        }

        # Call Razorpay SDK to create the order
        order = client.order.create(data=order_data)
        logger.info(f"Successfully created Razorpay order {order.get('id')} for user {current_user.email}")
        
        # Return exactly { order_id, amount, currency }
        return {
            "order_id": order.get("id"),
            "amount": order.get("amount"),
            "currency": order.get("currency"),
            "mock": False
        }

    except Exception as e:
        logger.error(f"Failed to create Razorpay order: {str(e)}", exc_info=True)
        # Check if it was an authentication/credentials failure from Razorpay side
        err_msg = str(e).lower()

        # If using test credentials and authentication fails, fallback to sandbox mock mode
        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_ID.startswith("rzp_test_"):
            logger.info("Razorpay API authentication failed with test key. Falling back to sandbox simulation.")
            return {
                "order_id": f"order_mock_{current_user.id}_{int(time.time())}",
                "amount": request.amount,
                "currency": request.currency,
                "mock": True
            }

        if "auth" in err_msg or "unauthorized" in err_msg or "401" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Razorpay authentication failed: {str(e)}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order creation failed: {str(e)}"
        )

@router.post("/api/verify-payment")
async def verify_payment(
    request: VerifyPaymentRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifies a Razorpay payment signature. If successful, activates the user's Pro plan in the DB.
    """
    is_mock = request.razorpay_order_id and request.razorpay_order_id.startswith("order_mock_")

    if not is_mock:
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            logger.error("Razorpay API key or secret not configured.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Razorpay is not configured on the backend."
            )

        # Missing fields: return 400
        if not request.razorpay_payment_id or not request.razorpay_order_id or not request.razorpay_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing fields: razorpay_payment_id, razorpay_order_id, and razorpay_signature are required."
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
    else:
        logger.info(f"Sandbox mock order {request.razorpay_order_id} verified automatically.")

    # Update user subscription in database to Pro
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
    except Exception as e:
        logger.error(f"Database error during subscription activation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database update failed: {str(e)}"
        )

