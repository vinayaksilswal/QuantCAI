from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.security import OAuth2PasswordBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import os
import logging
import re
from core import database as db
import models as DBmodels
from core.auth import (
    AuthSettings,
    verify_password,
    hash_password,
    issue_tokens,
    revoke_tokens_for_user,
    decode_token,
    rotate_refresh_token,
    get_current_user,
    verify_google_id_token,
    increment_failed_attempts,
    reset_failed_attempts,
    is_account_locked,
    lock_account,
)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)
auth_settings = AuthSettings()
ENV = os.getenv("ENV", "production").lower()
is_production = ENV == "production"

def get_db():
    ses = db.SessionLocal()
    try:
        yield ses
    finally:
        ses.close()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    is_blocked: bool
    role: str
    token_version: int

    class Config:
        from_attributes = True

class GoogleOAuthRequest(BaseModel):
    id_token: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None

@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, login_data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """User login with rate limiting and account lockout"""
    logger.info(f"Login attempt for email: {login_data.email}")
    try:
        user = db.query(DBmodels.User).filter(DBmodels.User.email == login_data.email).first()
        if not user:
            # Generic error to prevent user enumeration
            logger.warning(f"Login failed: User not found - {login_data.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Check if account is locked
        if is_account_locked(user):
            raise HTTPException(status_code=403, detail="Account is temporarily locked due to multiple failed login attempts. Please try again later.")

        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            # Increment failed attempts and check if we should lock
            attempts = increment_failed_attempts(user, db)
            if attempts >= auth_settings.max_failed_attempts:
                lock_account(user, db)
                logger.warning(f"Account locked: {user.email} after {attempts} failed attempts")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Successful login: reset failed attempts
        reset_failed_attempts(user, db)

        if user.is_blocked or not user.is_active:
            raise HTTPException(status_code=401, detail="Account is disabled")

        access, refresh = issue_tokens(db, user)

        samesite_val = "none" if is_production else "lax"
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=is_production,  # Dynamic based on env
            samesite=samesite_val,
            max_age=auth_settings.refresh_token_minutes * 60
        )

        logger.info(f"Login successful for user: {user.email} (ID: {user.id})")
        return TokenResponse(access_token=access, refresh_token="")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/register")
@limiter.limit("5/minute")
def register(request: Request, reg_data: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    """User registration with rate limiting and password complexity validation"""
    logger.info(f"Registration attempt for email: {reg_data.email}")
    try:
        # Password complexity validation
        password = reg_data.password
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password):
            raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            raise HTTPException(status_code=400, detail="Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise HTTPException(status_code=400, detail="Password must contain at least one special character")

        # Sanitize name field (allow basic characters only)
        if not re.match(r"^[a-zA-Z0-9\s\-\.\'\(\)]+$", reg_data.name):
            raise HTTPException(status_code=400, detail="Name contains invalid characters")

        user = db.query(DBmodels.User).filter(DBmodels.User.email == reg_data.email).first()
        if user:
            raise HTTPException(status_code=400, detail="User already exists")

        new_user = DBmodels.User(
            email=reg_data.email,
            hashed_password=hash_password(reg_data.password),
            name=reg_data.name.strip(),
            is_active=True,
            is_blocked=False,
            role=DBmodels.UserRole.LEARNER
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"Registration successful for user: {new_user.email} (ID: {new_user.id})")
        access, refresh = issue_tokens(db, new_user)

        samesite_val = "none" if is_production else "lax"
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=is_production,
            samesite=samesite_val,
            max_age=auth_settings.refresh_token_minutes * 60
        )

        return TokenResponse(access_token=access, refresh_token="")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/logout")
def logout(response: Response, current_user: DBmodels.User = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"Logout request for user {current_user.email}")
    try:
        # Re-fetch user in the local db session to avoid cross-session errors
        local_user = db.query(DBmodels.User).filter(DBmodels.User.id == current_user.id).first()
        if not local_user:
            raise HTTPException(status_code=404, detail="User not found")
        revoke_tokens_for_user(local_user, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Logout failed")
    samesite_val = "none" if is_production else "lax"
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=is_production,
        samesite=samesite_val
    )
    return {"message": "logout successful"}

@router.post("/refresh")
@limiter.limit("10/minute")
def refresh_tokens(request: Request, response: Response, db: Session = Depends(get_db)):
    """Refresh access token using httpOnly cookie. Rate limited."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = payload.get("sub")
        token_version = payload.get("token_version", 0)
        user = db.query(DBmodels.User).filter(DBmodels.User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if user.token_version != token_version:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

        access, new_refresh = rotate_refresh_token(db, payload, user)

        samesite_val = "none" if is_production else "lax"
        response.set_cookie(
            key="refresh_token",
            value=new_refresh,
            httponly=True,
            secure=is_production,
            samesite=samesite_val,
            max_age=auth_settings.refresh_token_minutes * 60
        )

        return TokenResponse(access_token=access, refresh_token="")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.get("/me", response_model=UserResponse)
def me(current_user: DBmodels.User = Depends(get_current_user)):
    logger.info("Me endpoint accessed")
    return UserResponse.model_validate(current_user)
