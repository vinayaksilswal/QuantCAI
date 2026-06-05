import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, Request, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import models as DBmodels
from core import database as db
from core.config import settings as core_settings


# Remove CryptContext and usage of passlib
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthSettings(BaseModel):
    """Auth-related settings loaded from environment variables."""

    secret_key: str = Field(default_factory=lambda: core_settings.SECRET_KEY)
    algorithm: str = Field(default_factory=lambda: core_settings.ALGORITHM)
    access_token_minutes: int = Field(default_factory=lambda: core_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_minutes: int = Field(default_factory=lambda: core_settings.REFRESH_TOKEN_EXPIRE_DAYS * 1440)
    google_client_id: Optional[str] = Field(default_factory=lambda: os.getenv("GOOGLE_CLIENT_ID"))
    google_client_secret: Optional[str] = Field(default_factory=lambda: os.getenv("GOOGLE_CLIENT_SECRET"))
    google_redirect_uri: Optional[str] = Field(default_factory=lambda: os.getenv("GOOGLE_REDIRECT_URI"))

    # Lockout policy
    max_failed_attempts: int = Field(default_factory=lambda: int(os.getenv("MAX_FAILED_ATTEMPTS", "5")))
    lockout_duration_minutes: int = Field(default_factory=lambda: int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")))


settings = AuthSettings()

# Security warning for production
if settings.secret_key == "change-me" or "change-me" in settings.secret_key:
    # In a real production scenario, you might want to raise an error.
    # For now, we print a warning so local dev works but the risk is known.
    print("WARNING: AUTH_SECRET_KEY is set to default 'change-me' value. This is unsafe for production!")


def get_db_session():
    """Dependency for DB session to avoid circular imports."""
    ses = db.SessionLocal()
    try:
        yield ses
    finally:
        ses.close()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # bcrypt requires bytes, so encode the password
    pwd_bytes = password.encode('utf-8')
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    # Return as string for storage
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a stored password against one provided by user."""
    try:
        pwd_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except (ValueError, TypeError):
        # Could happen if the hash in DB is invalid or empty
        return False


def get_subscription_plan_sync(db: Session, user_id: int, org_id: Optional[int]) -> str:
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import desc
    sub = (
        db.query(DBmodels.Subscription)
        .filter(
            (DBmodels.Subscription.user_id == user_id) |
            ((DBmodels.Subscription.org_id == org_id) & (DBmodels.Subscription.org_id.is_not(None)))
        )
        .filter(
            (DBmodels.Subscription.status == DBmodels.SubscriptionStatus.ACTIVE) |
            (
                (DBmodels.Subscription.status == DBmodels.SubscriptionStatus.PAST_DUE) &
                (DBmodels.Subscription.updated_at >= datetime.now(timezone.utc) - timedelta(days=3))
            )
        )
        .order_by(desc(DBmodels.Subscription.created_at))
        .first()
    )
    if sub:
        return sub.plan.value if hasattr(sub.plan, "value") else str(sub.plan)
    return "free"


def _create_token(
    user: DBmodels.User,
    token_type: str,
    expires_minutes: int,
    jti: Optional[str] = None,
    db: Optional[Session] = None,
) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    
    plan = "free"
    if db is not None:
        plan = get_subscription_plan_sync(db, user.id, user.org_id)

    to_encode = {
        "sub": str(user.id),
        "type": token_type,
        "role": user.role,
        "subscription_plan": plan,
        "token_version": user.token_version,
        "exp": expire,
    }
    if jti is not None:
        to_encode["jti"] = jti
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(user: DBmodels.User, db: Optional[Session] = None) -> str:
    return _create_token(user, "access", settings.access_token_minutes, db=db)


def create_refresh_token(user: DBmodels.User, jti: str, db: Optional[Session] = None) -> str:
    return _create_token(user, "refresh", settings.refresh_token_minutes, jti=jti, db=db)


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    request: Request, db: Session = Depends(get_db_session)
) -> DBmodels.User:
    """Extract bearer token from Authorization header, decode, and fetch user."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.removeprefix("Bearer ").strip()
    payload = decode_token(token, expected_type="access")
    user_id = payload.get("sub")
    token_version = payload.get("token_version", 0)

    user = db.query(DBmodels.User).filter(DBmodels.User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.is_blocked or not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive or blocked")
    if user.token_version != token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    return user


def revoke_tokens_for_user(user: DBmodels.User, db: Session) -> None:
    """Revoke all tokens for a user by bumping token_version and marking refresh tokens revoked."""
    user.token_version += 1
    db.add(user)
    db.query(DBmodels.RefreshToken).filter(DBmodels.RefreshToken.user_id == user.id).update(
        {"revoked": True}, synchronize_session=False
    )
    db.commit()
    db.refresh(user)


def increment_failed_attempts(user: DBmodels.User, db: Session) -> int:
    """Increment failed login attempts. Returns current count."""
    user.failed_login_attempts += 1
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.failed_login_attempts


def reset_failed_attempts(user: DBmodels.User, db: Session) -> None:
    """Reset failed login attempts after successful login."""
    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.add(user)
        db.commit()
        db.refresh(user)


def is_account_locked(user: DBmodels.User, db: Optional[Session] = None) -> bool:
    """Check if account is currently locked."""
    if user.locked_until:
        if user.locked_until > datetime.utcnow():
            return True
        # Lock expired, reset if db session is available
        if db is not None:
            user.locked_until = None
            user.failed_login_attempts = 0
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # No db session to clear expired lock; treat as unlocked
            user.locked_until = None
            user.failed_login_attempts = 0
    return False


def lock_account(user: DBmodels.User, db: Session, duration_minutes: Optional[int] = None) -> None:
    """Lock account for specified duration (uses default if None)."""
    if duration_minutes is None:
        duration_minutes = settings.lockout_duration_minutes
    user.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    db.add(user)
    db.commit()
    db.refresh(user)






def issue_tokens(db: Session, user: DBmodels.User) -> Tuple[str, str]:
    """Create an access token and a tracked refresh token for a user."""
    now = datetime.utcnow()
    jti = str(uuid.uuid4())
    refresh_expires_at = now + timedelta(minutes=settings.refresh_token_minutes)
    refresh_row = DBmodels.RefreshToken(
        user_id=user.id,
        jti=jti,
        created_at=now,
        expires_at=refresh_expires_at,
        revoked=False,
    )
    db.add(refresh_row)
    db.commit()
    db.refresh(refresh_row)

    access = create_access_token(user, db=db)
    refresh = create_refresh_token(user, jti=jti, db=db)
    return access, refresh


def rotate_refresh_token(db: Session, payload: dict, user: DBmodels.User) -> Tuple[str, str]:
    """Rotate a refresh token: revoke existing jti and issue a new one."""
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing identifier",
        )
    token_row = (
        db.query(DBmodels.RefreshToken)
        .filter(
            DBmodels.RefreshToken.user_id == user.id,
            DBmodels.RefreshToken.jti == jti,
        )
        .first()
    )
    now = datetime.utcnow()
    if (
        token_row is None
        or token_row.revoked
        or (token_row.expires_at is not None and token_row.expires_at < now)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is no longer valid",
        )

    token_row.revoked = True
    new_jti = str(uuid.uuid4())
    new_expires_at = now + timedelta(minutes=settings.refresh_token_minutes)
    new_row = DBmodels.RefreshToken(
        user_id=user.id,
        jti=new_jti,
        created_at=now,
        expires_at=new_expires_at,
        revoked=False,
    )
    db.add(new_row)
    db.commit()
    db.refresh(new_row)

    access = create_access_token(user, db=db)
    refresh = create_refresh_token(user, jti=new_jti, db=db)
    return access, refresh


def verify_google_id_token(id_token_str: str) -> dict:
    """Verify a Google ID token using google-auth."""
    if not settings.google_client_id:
        raise RuntimeError("GOOGLE_CLIENT_ID environment variable must be set for Google OAuth.")
    try:
        request = google_requests.Request()
        idinfo = google_id_token.verify_oauth2_token(
            id_token_str,
            request,
            settings.google_client_id,
        )
        issuer = idinfo.get("iss")
        if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
            raise ValueError("Wrong issuer.")
        return idinfo
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google ID token: {exc}",
        )
