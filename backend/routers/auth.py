from fastapi import APIRouter, Depends, HTTPException, Response, Request, status, Form
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

def get_cookie_settings(request: Request) -> tuple[bool, str]:
    """
    Returns (secure, samesite) values based on host.
    If running on localhost/127.0.0.1, SameSite=Lax and Secure=False.
    Otherwise (e.g. Render/production), SameSite=None and Secure=True to support cross-domain cookies.
    """
    host = request.headers.get("host", "").lower()
    origin = request.headers.get("origin", "").lower()
    referer = request.headers.get("referer", "").lower()
    
    is_localhost = "localhost" in host or "127.0.0.1" in host or "localhost" in origin or "127.0.0.1" in origin or "localhost" in referer or "127.0.0.1" in referer
    is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    
    if not is_localhost and is_https:
        return True, "none"
    return False, "lax"

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
    logger.info("Login attempt for email: [REDACTED]")
    # Pre-compute a dummy hash for timing-safe comparison when user is not found.
    # This prevents user enumeration via response time differences.
    _DUMMY_HASH = "$2b$12$FxRbyEr9aWmh8G2j2ndpN.Ks5E9vHmZB0vJPfGPw4X6bQvZdR5HXi"
    try:
        user = db.query(DBmodels.User).filter(DBmodels.User.email == login_data.email).first()
        if not user:
            # Run bcrypt anyway to make timing consistent with the "wrong password" path
            verify_password(login_data.password, _DUMMY_HASH)
            logger.warning(f"Login failed: User not found")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Check if account is locked
        if is_account_locked(user, db):
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

        secure_val, samesite_val = get_cookie_settings(request)
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=secure_val,
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
            role=DBmodels.UserRole.LEARNER,
            email_verified=False  # Explicitly set; verification email should be triggered
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"Registration successful for user: {new_user.email} (ID: {new_user.id})")
        access, refresh = issue_tokens(db, new_user)

        secure_val, samesite_val = get_cookie_settings(request)
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=secure_val,
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
def logout(request: Request, response: Response, current_user: DBmodels.User = Depends(get_current_user), db: Session = Depends(get_db)):
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
    secure_val, samesite_val = get_cookie_settings(request)
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=secure_val,
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

        secure_val, samesite_val = get_cookie_settings(request)
        response.set_cookie(
            key="refresh_token",
            value=new_refresh,
            httponly=True,
            secure=secure_val,
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

@router.get("/config")
def get_auth_config():
    """Expose public authentication settings to the frontend"""
    return {
        "google_client_id": auth_settings.google_client_id,
        "google_redirect_uri": auth_settings.google_redirect_uri
    }

@router.post("/oauth/google")
@limiter.limit("5/minute")
def oauth_google(request: Request, data: GoogleOAuthRequest, response: Response, db: Session = Depends(get_db)):
    """Google OAuth registration/login endpoint"""
    logger.info("Google OAuth login/registration attempt")
    try:
        if not data.id_token:
            # Check if we are in development and want to support email/name directly as a backup
            if not is_production and data.email:
                email = data.email
                name = data.name or email.split("@")[0]
            else:
                raise HTTPException(status_code=400, detail="Google id_token is required")
        else:
            # Verify the ID Token
            try:
                idinfo = verify_google_id_token(data.id_token)
            except Exception as e:
                logger.error(f"Google ID token verification failed: {e}")
                raise HTTPException(status_code=401, detail=f"Invalid Google ID token: {e}")
            
            email = idinfo.get("email")
            name = idinfo.get("name") or email.split("@")[0]
            
            if not email:
                raise HTTPException(status_code=400, detail="Google token does not contain email")

        # Find or create user
        user = db.query(DBmodels.User).filter(DBmodels.User.email == email).first()
        if not user:
            # Register a new user
            import secrets
            random_password = secrets.token_urlsafe(32)
            user = DBmodels.User(
                email=email,
                hashed_password=hash_password(random_password),
                name=name.strip(),
                is_active=True,
                is_blocked=False,
                role=DBmodels.UserRole.LEARNER,
                email_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Google OAuth registered new user: {user.email} (ID: {user.id})")
        else:
            # User exists
            if user.is_blocked or not user.is_active:
                raise HTTPException(status_code=401, detail="Account is disabled")
            
            # Reset failed attempts
            reset_failed_attempts(user, db)
            
            # Update name if changed or empty
            if name and not user.name:
                user.name = name.strip()
                db.add(user)
                db.commit()
                db.refresh(user)
                
            logger.info(f"Google OAuth login successful for user: {user.email} (ID: {user.id})")

        # Issue tokens
        access, refresh = issue_tokens(db, user)

        secure_val, samesite_val = get_cookie_settings(request)
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=secure_val,
            samesite=samesite_val,
            max_age=auth_settings.refresh_token_minutes * 60
        )

        return TokenResponse(access_token=access, refresh_token="")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


from fastapi.responses import HTMLResponse, RedirectResponse
from core.saml_config import SAML_SP_ENTITY_ID, SAML_SP_ACS_URL, SAML_IDP_SSO_URL, SAML_IDP_ENTITY_ID

@router.get("/saml/metadata", response_class=HTMLResponse)
def saml_metadata():
    """Generates standard SAML Service Provider metadata XML."""
    metadata_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" entityID="{SAML_SP_ENTITY_ID}">
    <md:SPSSODescriptor AuthnRequestsSigned="false" WantAssertionsSigned="true" protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
        <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" Location="{SAML_SP_ACS_URL}" index="1"/>
    </md:SPSSODescriptor>
</md:EntityDescriptor>
"""
    return HTMLResponse(content=metadata_xml, media_type="application/xml")


@router.get("/saml/login")
def saml_login():
    """Redirects the client browser to the corporate Identity Provider (IdP)."""
    redirect_url = f"{SAML_IDP_SSO_URL}?SAMLRequest=MockRequestPayload&RelayState={SAML_SP_ENTITY_ID}"
    return RedirectResponse(url=redirect_url)


@router.post("/saml/acs")
def saml_acs_callback(
    response: Response,
    SAMLResponse: str = Form(...),
    RelayState: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    SAML Assertion Consumer Service (ACS) callback.
    Decodes the corporate SAML Response, registers/finds the user, and redirects to the frontend.
    """
    logger.info("SAML SSO ACS Callback triggered.")
    
    import base64
    try:
        decoded_xml = base64.b64decode(SAMLResponse).decode('utf-8', errors='ignore')
        logger.info("Successfully decoded SAML assertion XML payload.")
    except Exception as parse_err:
        logger.warning(f"SAML decode assertion failed, using mock placeholder parsing: {parse_err}")
        decoded_xml = ""

    email = None
    name = None
    
    email_match = re.search(r'<saml:NameID[^>]*>([^<]+)</saml:NameID>', decoded_xml)
    if email_match:
        email = email_match.group(1).strip()
        name = email.split("@")[0].title()
    else:
        email_attr = re.search(r'<saml:Attribute Name="email"[^>]*>.*?<saml:AttributeValue[^>]*>([^<]+)</saml:AttributeValue>', decoded_xml, re.DOTALL)
        if email_attr:
            email = email_attr.group(1).strip()
            name = email.split("@")[0].title()
    
    # SECURITY: Never use hardcoded fallback emails — if parsing fails, reject the assertion
    if not email:
        logger.error("SAML ACS: Failed to extract email from SAML assertion")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SAML assertion does not contain a valid email address. "
                   "Please contact your IT administrator."
        )
    if not name:
        name = email.split("@")[0].title()

    user = db.query(DBmodels.User).filter(DBmodels.User.email == email).first()
    if not user:
        import secrets
        random_password = secrets.token_urlsafe(32)
        user = DBmodels.User(
            email=email,
            hashed_password=hash_password(random_password),
            name=name,
            is_active=True,
            is_blocked=False,
            role=DBmodels.UserRole.ENTERPRISE_USER,
            email_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"SAML registered new Enterprise user: {email}")
    else:
        if user.is_blocked or not user.is_active:
            raise HTTPException(status_code=403, detail="SAML user is blocked or inactive.")
        
        if user.role not in (DBmodels.UserRole.ROOT, DBmodels.UserRole.ADMIN, DBmodels.UserRole.ENTERPRISE_USER):
            user.role = DBmodels.UserRole.ENTERPRISE_USER
            db.add(user)
            db.commit()
            db.refresh(user)
            
        logger.info(f"SAML successfully logged in user: {email}")

    reset_failed_attempts(user, db)
    access, refresh = issue_tokens(db, user)

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").split(",")[0]
    redirect_target = f"{frontend_url}/auth/callback?sso=success&token={access}"
    
    response_redirect = RedirectResponse(url=redirect_target, status_code=status.HTTP_303_SEE_OTHER)
    
    response_redirect.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=auth_settings.refresh_token_minutes * 60
    )
    
    return response_redirect

