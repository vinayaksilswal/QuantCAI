import os
import sys
import pytest
import pytest_asyncio
from unittest.mock import patch
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select, text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models as DBmodels
from core.database import async_session_factory
from main import app
from core.config import settings

def get_unique_suffix():
    return os.urandom(4).hex()

@pytest_asyncio.fixture(scope="function")
async def seed_user():
    """
    Seeds a test user and returns their ID and email.
    Cleans up user after test finishes.
    """
    suffix = get_unique_suffix()
    email = f"wplus_test_{suffix}@example.com"
    
    async with async_session_factory() as session:
        user = DBmodels.User(
            email=email,
            hashed_password="mock_password_hash",
            name="WarriorPlus Test User",
            role=DBmodels.UserRole.LEARNER,
            is_active=True
        )
        session.add(user)
        await session.flush()
        user_id = user.id
        await session.commit()

    yield user_id, email

    # Cleanup seeded data
    async with async_session_factory() as session:
        await session.execute(text("DELETE FROM subscriptions WHERE user_id = :uid"), {"uid": user_id})
        await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
        await session.commit()

@pytest.fixture(autouse=True)
def set_warriorplus_security_key():
    # Set a mock security key for tests
    original_key = settings.WARRIORPLUS_SECURITY_KEY
    settings.WARRIORPLUS_SECURITY_KEY = "test_secret_key_123"
    yield
    settings.WARRIORPLUS_SECURITY_KEY = original_key

@pytest.mark.asyncio
async def test_warriorplus_ipn_invalid_security_key():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Send IPN with incorrect security key
        response = await client.post(
            "/api/payment/warriorplus/ipn",
            data={
                "WP_SECURITYKEY": "wrong_key",
                "WP_ACTION": "sale",
                "WP_BUYER_EMAIL": "test@example.com",
                "WP_PAYMENT_STATUS": "Completed"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid security key" in response.json()["detail"]

@pytest.mark.asyncio
async def test_warriorplus_ipn_sale_existing_user(seed_user):
    user_id, email = seed_user
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Send successful sale IPN for existing user
        response = await client.post(
            "/api/payment/warriorplus/ipn",
            data={
                "WP_SECURITYKEY": "test_secret_key_123",
                "WP_ACTION": "sale",
                "WP_BUYER_EMAIL": email,
                "WP_BUYER_NAME": "WarriorPlus Test User",
                "WP_SALEID": "sale12345",
                "WP_PAYMENT_STATUS": "Completed",
                "WP_ITEM_NUMBER": "wso_rrynld"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

        # Verify db updated subscription to PRO
        async with async_session_factory() as session:
            stmt = select(DBmodels.Subscription).where(DBmodels.Subscription.user_id == user_id)
            res = await session.execute(stmt)
            sub = res.scalar_one_or_none()
            assert sub is not None
            assert sub.plan == DBmodels.SubscriptionPlan.PRO
            assert sub.status == DBmodels.SubscriptionStatus.ACTIVE
            assert sub.stripe_subscription_id == "warriorplus_sale12345"

@pytest.mark.asyncio
async def test_warriorplus_ipn_sale_new_user():
    suffix = get_unique_suffix()
    new_email = f"new_wplus_user_{suffix}@example.com"

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Send successful sale IPN for new user
        response = await client.post(
            "/api/payment/warriorplus/ipn",
            data={
                "WP_SECURITYKEY": "test_secret_key_123",
                "WP_ACTION": "sale",
                "WP_BUYER_EMAIL": new_email,
                "WP_BUYER_NAME": "New WPlus Customer",
                "WP_SALEID": "sale_new_123",
                "WP_PAYMENT_STATUS": "Completed",
                "WP_ITEM_NUMBER": "wso_rrynld"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

        # Verify new user and subscription were created in database
        async with async_session_factory() as session:
            stmt_user = select(DBmodels.User).where(DBmodels.User.email == new_email)
            res_user = await session.execute(stmt_user)
            user = res_user.scalar_one_or_none()
            assert user is not None
            assert user.name == "New WPlus Customer"

            stmt_sub = select(DBmodels.Subscription).where(DBmodels.Subscription.user_id == user.id)
            res_sub = await session.execute(stmt_sub)
            sub = res_sub.scalar_one_or_none()
            assert sub is not None
            assert sub.plan == DBmodels.SubscriptionPlan.PRO
            assert sub.status == DBmodels.SubscriptionStatus.ACTIVE
            assert sub.stripe_subscription_id == "warriorplus_sale_new_123"

            # Cleanup newly created user and subscription
            await session.execute(text("DELETE FROM subscriptions WHERE user_id = :uid"), {"uid": user.id})
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user.id})
            await session.commit()

@pytest.mark.asyncio
async def test_warriorplus_ipn_refund(seed_user):
    user_id, email = seed_user
    
    # Pre-create active PRO subscription
    async with async_session_factory() as session:
        sub = DBmodels.Subscription(
            user_id=user_id,
            plan=DBmodels.SubscriptionPlan.PRO,
            status=DBmodels.SubscriptionStatus.ACTIVE,
            stripe_subscription_id="warriorplus_sale12345"
        )
        session.add(sub)
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Send refund/cancel action
        response = await client.post(
            "/api/payment/warriorplus/ipn",
            data={
                "WP_SECURITYKEY": "test_secret_key_123",
                "WP_ACTION": "refund",
                "WP_BUYER_EMAIL": email,
                "WP_BUYER_NAME": "WarriorPlus Test User",
                "WP_SALEID": "sale12345",
                "WP_PAYMENT_STATUS": "Refunded"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

        # Verify db updated subscription to FREE (Cancelled)
        async with async_session_factory() as session:
            stmt = select(DBmodels.Subscription).where(DBmodels.Subscription.user_id == user_id)
            res = await session.execute(stmt)
            sub = res.scalar_one_or_none()
            assert sub is not None
            assert sub.plan == DBmodels.SubscriptionPlan.FREE
            assert sub.status == DBmodels.SubscriptionStatus.CANCELLED
