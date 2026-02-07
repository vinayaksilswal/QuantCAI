from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
import logging
import database as db
import DBmodels
from auth_utils import (
    AuthSettings,
    verify_password,
    hash_password,
    issue_tokens,
    revoke_tokens_for_user,
    decode_token,
    rotate_refresh_token,
    get_current_user,
    verify_google_id_token
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)
auth_settings = AuthSettings()

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

@router.post("/login", response_model=TokenResponse)
def login(request: Request, login_data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    logger.info(f"Login attempt for email: {login_data.email}")
    try:
        user = db.query(DBmodels.User).filter(DBmodels.User.email == login_data.email).first()
        if not user or not verify_password(login_data.password, user.password):
            logger.warning(f"Login failed: Invalid credentials - {login_data.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        if user.is_blocked or not user.is_active:
            raise HTTPException(status_code=401, detail="Account is disabled")

        access, refresh = issue_tokens(db, user)
        
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=False, 
            samesite="lax",
            max_age=auth_settings.refresh_token_minutes * 60
        )
        
        logger.info(f"Login successful for user: {user.email} (ID: {user.id})")
        return TokenResponse(access_token=access, refresh_token="")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/register", response_model=TokenResponse)
def register(request: Request, reg_data: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    logger.info(f"Registration attempt for email: {reg_data.email}")
    try:
        user = db.query(DBmodels.User).filter(DBmodels.User.email == reg_data.email).first()
        if user:
            raise HTTPException(status_code=400, detail="User already exists")

        new_user = DBmodels.User(
            email=reg_data.email, 
            password=hash_password(reg_data.password), 
            name=reg_data.name, 
            is_active=True, 
            is_blocked=False, 
            role="user"
        )
        db.add(new_user)  
        db.commit()
        db.refresh(new_user)
        logger.info(f"Registration successful for user: {new_user.email} (ID: {new_user.id})")
        access, refresh = issue_tokens(db, new_user)
        
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=False,
            samesite="lax",
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
    revoke_tokens_for_user(current_user, db)
    response.delete_cookie(key="refresh_token")
    return {"message": "logout successful"}

@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
        
    payload = decode_token(refresh_token, expected_type="refresh")
    user_id = payload.get("sub")
    token_version = payload.get("token_version", 0)
    user = db.query(DBmodels.User).filter(DBmodels.User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.token_version != token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
        
    access, new_refresh = rotate_refresh_token(db, payload, user)
    
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=auth_settings.refresh_token_minutes * 60
    )
    
    return TokenResponse(access_token=access, refresh_token="")

@router.get("/me", response_model=UserResponse)
def me(current_user: DBmodels.User = Depends(get_current_user)):
    logger.info("Me endpoint accessed")
    return UserResponse.model_validate(current_user)

@router.post("/oauth/google")
def oauth_google(request: GoogleOAuthRequest, db: Session = Depends(get_db)):
    logger.info(f"Google OAuth request using client_id={auth_settings.google_client_id or 'unset'}")
    if not request.id_token:
        raise HTTPException(status_code=400, detail="id_token is required")

    idinfo = verify_google_id_token(request.id_token)
    email = idinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google token did not contain an email")
    name = request.name or idinfo.get("name") or email.split("@")[0]

    user = db.query(DBmodels.User).filter(DBmodels.User.email == email).first()
    if not user:
        user = DBmodels.User(
            email=email,
            name=name,
            password=hash_password(os.urandom(16).hex()),
            is_active=True,
            is_blocked=False,
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    access, refresh = issue_tokens(db, user)
    return TokenResponse(access_token=access, refresh_token=refresh)
