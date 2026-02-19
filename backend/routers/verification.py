"""
Email verification endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import logging
import uuid
from datetime import datetime, timedelta
import os

import DBmodels
import database as db
from auth_utils import get_current_user, AuthSettings

router = APIRouter(prefix="/api/auth/verify", tags=["verification"])
logger = logging.getLogger(__name__)
auth_settings = AuthSettings()

def get_db():
    ses = db.SessionLocal()
    try:
        yield ses
    finally:
        ses.close()

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class VerifyEmailRequest(BaseModel):
    token: str

def send_verification_email(user: DBmodels.User, token: str, request: Request = None):
    """
    Send verification email to user.
    In production, integrate with SendGrid/Mailgun/SMTP.
    For now, just log and maybe return the link for testing.
    """
    verification_link = f"{request.base_url if request else 'https://quantcai.in'}/verify-email?token={token}"
    
    # TODO: Integrate actual email sending
    # Example with SendGrid:
    # from sendgrid import SendGridAPIClient
    # from sendgrid.helpers.mail import Mail, Email, To, Content
    # message = Mail(
    #     from_email="noreply@quantcai.in",
    #     to_emails=user.email,
    #     subject="Verify your QuantCAI email",
    #     html_content=f"<p>Click <a href='{verification_link}'>here</a> to verify.</p>")
    # sg.send(message)

    logger.info(f"Verification email would be sent to {user.email} with link: {verification_link}")
    return verification_link

@router.post("/send")
def send_verification(
    request: Request,
    current_user: DBmodels.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send verification email to current user."""
    if current_user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    # Create verification token
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry

    # Invalidate any old tokens for this user
    db.query(DBmodels.EmailVerificationToken).filter(
        DBmodels.EmailVerificationToken.user_id == current_user.id
    ).delete(synchronize_session=False)

    verification_token = DBmodels.EmailVerificationToken(
        user_id=current_user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(verification_token)
    current_user.verification_sent_at = datetime.utcnow()
    db.add(current_user)
    db.commit()

    # Send email
    link = send_verification_email(current_user, token, request)

    logger.info(f"Verification email sent to {current_user.email}")
    return {
        "message": "Verification email sent",
        "expires_at": expires_at.isoformat()
    }

@router.post("/resend")
def resend_verification(
    req: ResendVerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Resend verification email (for unverified users who haven't logged in yet)."""
    user = db.query(DBmodels.User).filter(DBmodels.User.email == req.email).first()
    if not user:
        # Don't reveal whether email exists
        return {"message": "If that email exists, we've sent a verification link"}

    if user.email_verified:
        return {"message": "Email already verified"}

    # Create new token (delete old ones)
    db.query(DBmodels.EmailVerificationToken).filter(
        DBmodels.EmailVerificationToken.user_id == user.id
    ).delete(synchronize_session=False)

    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)

    verification_token = DBmodels.EmailVerificationToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(verification_token)
    user.verification_sent_at = datetime.utcnow()
    db.add(user)
    db.commit()

    link = send_verification_email(user, token, request)
    logger.info(f"Verification email resent to {user.email}")

    return {"message": "Verification email sent"}

@router.post("/confirm")
def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """Verify email using token."""
    token_record = db.query(DBmodels.EmailVerificationToken).filter(
        DBmodels.EmailVerificationToken.token == request.token
    ).first()

    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    if token_record.expires_at < datetime.utcnow():
        db.delete(token_record)
        db.commit()
        raise HTTPException(status_code=400, detail="Verification token expired")

    user = db.query(DBmodels.User).filter(DBmodels.User.id == token_record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email_verified = True
    user.verification_sent_at = None  # Clear sent timestamp
    db.add(user)
    db.delete(token_record)  # One-time use
    db.commit()

    logger.info(f"Email verified for user {user.email}")
    return {"message": "Email verified successfully"}

@router.get("/status")
def verification_status(
    current_user: DBmodels.User = Depends(get_current_user)
):
    """Check current user's email verification status."""
    return {
        "email_verified": current_user.email_verified,
        "verification_sent_at": current_user.verification_sent_at.isoformat() if current_user.verification_sent_at else None
    }
