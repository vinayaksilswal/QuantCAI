import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models as DBmodels
from core.database import async_session_factory, engine
from security import (
    generate_api_key,
    hash_api_key,
    verify_api_key,
    create_access_token,
    create_refresh_token,
    get_subscription_plan,
    get_current_user,
    get_api_key_user
)
from middleware import (
    RapidAPIValidationMiddleware,
    custom_key_func,
    get_rate_limit
)
from core.auth import verify_password
from routers.auth import router as auth_router

# Setup a dummy FastAPI app for routing and middleware tests
app = FastAPI()
app.add_middleware(RapidAPIValidationMiddleware)
app.include_router(auth_router)

@app.get("/test-jwt")
async def handle_test_jwt(current_user: DBmodels.User = Depends(get_current_user)):
    return {"user_id": current_user.id, "email": current_user.email}

@app.get("/test-apikey")
async def handle_test_apikey(current_user: DBmodels.User = Depends(get_api_key_user)):
    return {"user_id": current_user.id, "email": current_user.email}

# -----------------------------------------------------------------------------
# 1. JWT and Hashing Cryptography Tests
# -----------------------------------------------------------------------------
def test_password_verification():
    # Test bcrypt hashing compatibility
    password = "MySecurePassword123!"
    import bcrypt
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_pwd", hashed) is False

def test_api_key_generation_and_hashing():
    # Format verification: qcai_ + 32 urlsafe characters
    api_key = generate_api_key()
    assert api_key.startswith("qcai_")
    assert len(api_key) == 37  # 5 prefix + 32 characters

    # Deterministic hashing check
    h1 = hash_api_key(api_key)
    h2 = hash_api_key(api_key)
    assert h1 == h2
    assert verify_api_key(api_key, h1) is True
    assert verify_api_key("wrong_key", h1) is False

def test_jwt_generation_and_payload():
    payload = {
        "user_id": 42,
        "email": "test@quantcai.com",
        "role": "developer",
        "org_id": 10,
        "subscription_plan": "pro"
    }
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    assert access_token is not None
    assert refresh_token is not None

# -----------------------------------------------------------------------------
# 2. Database Integration Tests (Seeded test user & keys)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_database_auth_flow():
    # Setup test models in real DB
    suffix = os.urandom(4).hex()
    email = f"dev_{suffix}@example.com"
    import bcrypt
    hashed_pwd = bcrypt.hashpw("Password123!".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    async with async_session_factory() as session:
        # Create user
        user = DBmodels.User(
            email=email,
            hashed_password=hashed_pwd,
            name="Developer User",
            role=DBmodels.UserRole.DEVELOPER,
            is_active=True,
            is_blocked=False
        )
        session.add(user)
        await session.flush()

        # Create active subscription
        sub = DBmodels.Subscription(
            user_id=user.id,
            plan=DBmodels.SubscriptionPlan.PRO,
            status=DBmodels.SubscriptionStatus.ACTIVE
        )
        session.add(sub)

        # Create API key
        raw_key = generate_api_key()
        hashed_key = hash_api_key(raw_key)
        api_key = DBmodels.APIKey(
            user_id=user.id,
            key_hash=hashed_key,
            label="Test Key",
            tier=DBmodels.APIKeyTier.PRO,
            daily_limit=10,
            requests_today=0,
            is_active=True
        )
        session.add(api_key)
        await session.commit()

        user_id = user.id
        org_id = user.org_id
        api_key_id = api_key.id

    try:
        # Test get_subscription_plan helper
        async with async_session_factory() as session:
            plan = await get_subscription_plan(session, user_id, org_id)
            assert plan == "pro"

        # Test Login router endpoint manually using AsyncClient
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            login_res = await client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
            assert login_res.status_code == 200
            assert "access_token" in login_res.json()
            assert "refresh_token" in login_res.cookies

        # Test dependency: get_current_user with JWT
        token = login_res.json()["access_token"]
        request = MagicMock(spec=Request)
        request.headers = {"Authorization": f"Bearer {token}"}
        request.state = MagicMock()

        async with async_session_factory() as session:
            db_user = await get_current_user(request, session)
            assert db_user.id == user_id
            assert request.state.user_id == user_id
            assert request.state.tier == "pro"

        # Test dependency: get_api_key_user with X-API-Key
        key_request = MagicMock(spec=Request)
        key_request.headers = {"X-API-Key": raw_key}
        key_request.state = MagicMock()

        async with async_session_factory() as session:
            key_user = await get_api_key_user(key_request, session)
            assert key_user.id == user_id
            assert key_request.state.api_key_id == api_key_id
            assert key_request.state.tier == "pro"

            # Check that requests_today was incremented atomically
            refetched_key_res = await session.execute(
                select(DBmodels.APIKey).where(DBmodels.APIKey.id == api_key_id)
            )
            refetched_key = refetched_key_res.scalar_one()
            assert refetched_key.requests_today == 1

        # Test API Key limit enforcement (requests_today >= daily_limit)
        async with async_session_factory() as session:
            stmt = select(DBmodels.APIKey).where(DBmodels.APIKey.id == api_key_id)
            res = await session.execute(stmt)
            k = res.scalar_one()
            k.requests_today = 10  # Equal to limit
            session.add(k)
            await session.commit()

        async with async_session_factory() as session:
            with pytest.raises(HTTPException) as exc_info:
                await get_api_key_user(key_request, session)
            assert exc_info.value.status_code == 429
            assert "limit exceeded" in exc_info.value.detail

    finally:
        # Cleanup seeded data
        async with async_session_factory() as session:
            await session.execute(
                select(DBmodels.APIKey).where(DBmodels.APIKey.user_id == user_id)
            )
            await session.execute(
                select(DBmodels.Subscription).where(DBmodels.Subscription.user_id == user_id)
            )
            await session.execute(
                select(DBmodels.User).where(DBmodels.User.id == user_id)
            )
            await session.commit()

# -----------------------------------------------------------------------------
# 3. RapidAPI Validation Middleware Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
@patch("middleware.redis_client", new_callable=AsyncMock)
async def test_rapidapi_middleware(mock_redis):
    from core.config import settings
    original_secret = settings.RAPIDAPI_PROXY_SECRET
    settings.RAPIDAPI_PROXY_SECRET = "secret123"
    try:
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # A. Valid Secret
            mock_redis.setex = AsyncMock(return_value=True)
            res = await client.get("/test-jwt", headers={
                "X-RapidAPI-Proxy-Secret": "secret123",
                "X-RapidAPI-User": "user_id_456"
            })
            # Should bypass middleware and hit route auth (which fails with 401 JWT missing, meaning middleware let it through)
            assert res.status_code == 401
            assert "Missing or invalid Authorization header" in res.json()["detail"]
            mock_redis.setex.assert_called_with("rapidapi_session:user_id_456", 30, "1")

            # B. Invalid Secret
            res = await client.get("/test-jwt", headers={
                "X-RapidAPI-Proxy-Secret": "wrong_secret"
            })
            assert res.status_code == 401
            assert "Invalid X-RapidAPI-Proxy-Secret" in res.json()["detail"]

            # C. Missing Secret, active Redis session
            mock_redis.get = AsyncMock(return_value="1")
            res = await client.get("/test-jwt", headers={
                "X-RapidAPI-User": "user_id_456"
            })
            assert res.status_code == 401  # Let through to jwt auth check
            assert "Missing or invalid Authorization header" in res.json()["detail"]
            mock_redis.get.assert_called_with("rapidapi_session:user_id_456")

            # D. Missing Secret, expired/missing Redis session
            mock_redis.get = AsyncMock(return_value=None)
            res = await client.get("/test-jwt", headers={
                "X-RapidAPI-User": "user_id_456"
            })
            assert res.status_code == 401
            assert "no valid session cached in Redis" in res.json()["detail"]
    finally:
        settings.RAPIDAPI_PROXY_SECRET = original_secret

# -----------------------------------------------------------------------------
# 4. Slowapi Rate Limiting Config Tests
# -----------------------------------------------------------------------------
def test_rate_limiting_keys_and_tiers():
    request = MagicMock(spec=Request)
    request.state = MagicMock()

    # Test key resolution
    # Case A: API Key user
    request.state.api_key_id = 99
    assert custom_key_func(request) == "apikey:99"

    # Case B: JWT user
    delattr(request.state, "api_key_id")
    request.state.user_id = 111
    assert custom_key_func(request) == "user:111"

    # Case C: Unauthenticated IP fallback
    delattr(request.state, "user_id")
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    assert custom_key_func(request) == "127.0.0.1"

    # Test dynamic rate limit resolution
    # Case A: free
    request.state.tier = "free"
    assert get_rate_limit(request) == "20/minute"

    # Case B: pro
    request.state.tier = "pro"
    assert get_rate_limit(request) == "200/minute"

    # Case C: enterprise
    request.state.tier = "enterprise"
    assert get_rate_limit(request) == "2000/minute"
