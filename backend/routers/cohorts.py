import logging
import httpx
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

import models as DBmodels
from core.database import get_db
from core.auth import get_current_user
from core.config import settings
from routers.paypal_billing import _get_paypal_access_token, _paypal_base_url

logger = logging.getLogger("quantcai.cohorts")
router = APIRouter(prefix="/api/v1/cohorts", tags=["Cohorts & Education"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class CohortResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    capacity: Optional[int] = None
    enrollment_status: str
    zoom_link: Optional[str] = None
    is_enrolled: bool

    class Config:
        from_attributes = True

class EnrollRequest(BaseModel):
    course_id: int

class CaptureEnrollRequest(BaseModel):
    order_id: str
    course_id: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=List[CohortResponse])
async def list_cohorts(
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all active courses/cohorts and check the current user's enrollment status."""
    # Fetch active courses
    stmt = select(DBmodels.Course).where(DBmodels.Course.is_active == True).order_by(DBmodels.Course.start_date.asc())
    res = await db.execute(stmt)
    courses = res.scalars().all()

    # Fetch user's active enrollments
    enroll_stmt = select(DBmodels.CohortEnrollment).where(
        DBmodels.CohortEnrollment.user_id == current_user.id,
        DBmodels.CohortEnrollment.payment_status == "completed"
    )
    enroll_res = await db.execute(enroll_stmt)
    enrollments = enroll_res.scalars().all()
    enrolled_course_ids = {e.course_id for e in enrollments}

    response = []
    for c in courses:
        enrolled = c.id in enrolled_course_ids
        response.append(CohortResponse(
            id=c.id,
            title=c.title,
            description=c.description,
            start_date=c.start_date.isoformat() if c.start_date else None,
            end_date=c.end_date.isoformat() if c.end_date else None,
            capacity=c.capacity,
            enrollment_status=c.enrollment_status,
            zoom_link=c.zoom_link if enrolled else None,  # Only expose zoom link to enrolled participants
            is_enrolled=enrolled
        ))

    return response


@router.post("/enroll")
async def enroll_in_cohort(
    body: EnrollRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a PayPal order for cohort enrollment ($1,500.00 USD).
    Returns the PayPal approval URL.
    """
    # Fetch course
    stmt = select(DBmodels.Course).where(DBmodels.Course.id == body.course_id, DBmodels.Course.is_active == True)
    res = await db.execute(stmt)
    course = res.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Cohort course not found")

    if course.enrollment_status != "open":
        raise HTTPException(status_code=400, detail="Enrollment is currently closed for this cohort.")

    # Check if user already enrolled
    check_stmt = select(DBmodels.CohortEnrollment).where(
        DBmodels.CohortEnrollment.user_id == current_user.id,
        DBmodels.CohortEnrollment.course_id == body.course_id,
        DBmodels.CohortEnrollment.payment_status == "completed"
    )
    check_res = await db.execute(check_stmt)
    if check_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You are already enrolled in this cohort.")

    # Create PayPal Order
    access_token = await _get_paypal_access_token()
    frontend_url = settings.FRONTEND_URL.split(",")[0]

    cohort_price = 1500.00 # Standard cohort program price
    
    order_payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "USD",
                    "value": f"{cohort_price:.2f}"
                },
                "description": f"Applied Quantum Software Engineering Cohort - {course.title} (User ID {current_user.id})"
            }
        ],
        "application_context": {
            "brand_name": "QuantCAI Education",
            "locale": "en-US",
            "user_action": "PAY_NOW",
            "return_url": f"{frontend_url}/learn?enroll=success&course={course.id}",
            "cancel_url": f"{frontend_url}/learn?enroll=cancel"
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
        logger.error(f"PayPal Order creation failed for cohort: {resp.status_code} {resp.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to initiate PayPal payment for cohort."
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

    # Insert pending enrollment record
    enroll_stmt = select(DBmodels.CohortEnrollment).where(
        DBmodels.CohortEnrollment.user_id == current_user.id,
        DBmodels.CohortEnrollment.course_id == body.course_id
    )
    enroll_res = await db.execute(enroll_stmt)
    db_enroll = enroll_res.scalar_one_or_none()

    if not db_enroll:
        db_enroll = DBmodels.CohortEnrollment(
            user_id=current_user.id,
            course_id=body.course_id,
            payment_status="pending",
            payment_id=order_data.get("id")
        )
        db.add(db_enroll)
    else:
        db_enroll.payment_id = order_data.get("id")
        db_enroll.payment_status = "pending"
        db.add(db_enroll)

    await db.commit()

    return {
        "url": approval_url,
        "order_id": order_data.get("id")
    }


@router.post("/capture")
async def capture_cohort_enrollment(
    body: CaptureEnrollRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Capture a cohort enrollment order payment and complete the enrollment."""
    # Fetch pending enrollment
    stmt = select(DBmodels.CohortEnrollment).where(
        DBmodels.CohortEnrollment.user_id == current_user.id,
        DBmodels.CohortEnrollment.course_id == body.course_id
    )
    res = await db.execute(stmt)
    db_enroll = res.scalar_one_or_none()

    if not db_enroll:
        raise HTTPException(status_code=404, detail="Enrollment record not found.")

    if db_enroll.payment_status == "completed":
        return {"status": "already_completed", "message": "You are already enrolled in this cohort."}

    # Verify order ID match
    if db_enroll.payment_id != body.order_id:
         raise HTTPException(status_code=400, detail="Provided Order ID does not match enrollment record.")

    # Call PayPal to capture order
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
        # Fallback check
        async with httpx.AsyncClient() as check_client:
            check_resp = await check_client.get(
                f"{_paypal_base_url()}/v2/checkout/orders/{body.order_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=15.0
            )
        
        if check_resp.status_code == 200:
            order_details = check_resp.json()
            if order_details.get("status") == "COMPLETED":
                # Already captured on PayPal side, we can proceed with completion
                return await _complete_enrollment(db, db_enroll)
        
        logger.error(f"PayPal cohort capture failed: {resp.status_code} {resp.text}")
        raise HTTPException(status_code=502, detail="Failed to capture payment with PayPal.")

    capture_data = resp.json()
    status_str = capture_data.get("status")
    
    if status_str != "COMPLETED":
        raise HTTPException(status_code=400, detail=f"PayPal transaction status is '{status_str}', not 'COMPLETED'.")

    return await _complete_enrollment(db, db_enroll)


async def _complete_enrollment(db: AsyncSession, db_enroll: DBmodels.CohortEnrollment):
    db_enroll.payment_status = "completed"
    db.add(db_enroll)
    await db.commit()
    await db.refresh(db_enroll)

    logger.info(f"User {db_enroll.user_id} successfully enrolled in course {db_enroll.course_id}.")
    
    return {"status": "success", "message": "Enrollment completed successfully!"}
