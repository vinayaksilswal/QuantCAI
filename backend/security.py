import bcrypt
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models as DBmodels
from core.database import get_db
import redis.asyncio as aioredis
from core.config import settings

logger = logging.getLogger(__name__)

# Environment configuration
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

# Redis client configuration
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

# -----------------------------------------------------------------------------
# API Key Cryptography
# -----------------------------------------------------------------------------
# Bcrypt hashes are random by design, preventing direct database indexed lookups.
# To query by hash in O(1) time without performing slow O(N) table scans,
# we use a deterministic salt for hashing the developer API keys.
API_KEY_SALT = b"$2b$12$FxRbyEr9aWmh8G2j2ndpN."  # Must be exactly 22 base64 characters

def generate_api_key() -> str:
    """
    Generate a new API key of format 'qcai_' + 32 random URL-safe characters.
    """
    return f"qcai_{secrets.token_urlsafe(24)}"

def hash_api_key(api_key: str) -> str:
    """
    Hash an API key deterministically using bcrypt with a fixed salt.
    """
    key_bytes = api_key.encode("utf-8")
    hashed = bcrypt.hashpw(key_bytes, API_KEY_SALT)
    return hashed.decode("utf-8")

def verify_api_key(api_key: str, key_hash: str) -> bool:
    """
    Verify an API key against its hash using standard bcrypt comparison.
    """
    try:
        return bcrypt.checkpw(api_key.encode("utf-8"), key_hash.encode("utf-8"))
    except Exception:
        return False

# -----------------------------------------------------------------------------
# JWT Tokens
# -----------------------------------------------------------------------------
def create_access_token(data: dict) -> str:
    """
    Generate a JWT access token with 15 minutes expiration.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": int(expire.timestamp())})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """
    Generate a JWT refresh token with 30 days expiration.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": int(expire.timestamp())})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

# -----------------------------------------------------------------------------
# Subscription Tier Helper
# -----------------------------------------------------------------------------
async def get_subscription_plan(db: AsyncSession, user_id: int, org_id: Optional[int]) -> str:
    """
    Query the active subscription for the user or their organization.
    Defaults to 'free' if no active subscription is found.
    """
    # Active user-level subscription or active organization-level subscription
    stmt = (
        select(DBmodels.Subscription)
        .where(
            (DBmodels.Subscription.user_id == user_id) |
            ((DBmodels.Subscription.org_id == org_id) & (DBmodels.Subscription.org_id.is_not(None)))
        )
        .where(
            (DBmodels.Subscription.status == DBmodels.SubscriptionStatus.ACTIVE) |
            (
                (DBmodels.Subscription.status == DBmodels.SubscriptionStatus.PAST_DUE) &
                (DBmodels.Subscription.updated_at >= datetime.now(timezone.utc) - timedelta(days=3))
            )
        )
        .order_by(DBmodels.Subscription.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if sub:
        return sub.plan.value if hasattr(sub.plan, "value") else str(sub.plan)
    return "free"

# -----------------------------------------------------------------------------
# Security Dependencies
# -----------------------------------------------------------------------------
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> DBmodels.User:
    """
    FastAPI dependency that decodes JWT access tokens and returns the active user.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing user identity",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    stmt = select(DBmodels.User).where(DBmodels.User.id == int(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active or user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or blocked"
        )
        
    # Inject metadata into request.state for rate limiting and auditing
    request.state.user_id = user.id
    tier = payload.get("subscription_plan")
    if not tier:
        tier = await get_subscription_plan(db, user.id, user.org_id)
    request.state.tier = tier
    
    return user

async def get_api_key_user(request: Request, db: AsyncSession = Depends(get_db)) -> DBmodels.User:
    """
    FastAPI dependency that decodes API keys, validates tiers/limits,
    and returns the associated user. Increments the request count atomically.
    """
    api_key_val = request.headers.get("X-API-Key")
    if not api_key_val:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is missing"
        )

    # Hash the key to lookup using deterministic salt
    key_hash = hash_api_key(api_key_val)

    # Atomically lock the row to avoid race conditions on daily counter increments
    stmt = (
        select(DBmodels.APIKey)
        .where(DBmodels.APIKey.key_hash == key_hash)
        .with_for_update()
    )
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )

    if not api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key is inactive"
        )

    if api_key.requests_today >= api_key.daily_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily API request limit exceeded"
        )

    # Increment request count atomically
    api_key.requests_today += 1
    api_key.last_used_at = datetime.now(timezone.utc)
    db.add(api_key)
    await db.commit()

    # Load associated user details
    user_stmt = select(DBmodels.User).where(DBmodels.User.id == api_key.user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user or not user.is_active or user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account associated with this API key is inactive or blocked"
        )

    # Cache details in request state for slowapi key_func / rate limits
    request.state.api_key_id = api_key.id
    request.state.user_id = user.id
    request.state.tier = api_key.tier.value if hasattr(api_key.tier, "value") else str(api_key.tier)

    return user

async def get_current_user_or_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> DBmodels.User:
    """
    FastAPI dependency that allows authentication via either:
    1. Standard JWT bearer token in the Authorization header (for direct frontend users)
    2. API Key in the X-API-Key header (for external API developers)
    """
    api_key_val = request.headers.get("X-API-Key")
    auth_header = request.headers.get("Authorization")

    if api_key_val:
        return await get_api_key_user(request, db)
    elif auth_header and auth_header.startswith("Bearer "):
        return await get_current_user(request, db)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided. Send JWT in 'Authorization' header or API Key in 'X-API-Key' header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
