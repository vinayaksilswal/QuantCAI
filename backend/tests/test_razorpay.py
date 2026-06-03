import os
import sys
import pytest
import pytest_asyncio
import time
from unittest.mock import patch, MagicMock
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import text
from razorpay.errors import SignatureVerificationError

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models as DBmodels
from core.database import async_session_factory
from main import app  # imports main app with router registered
from security import create_access_token

def get_unique_suffix():
    return os.urandom(4).hex()

@pytest_asyncio.fixture(scope="function")
async def seed_user():
    """
    Seeds a test user and returns their ID and access token.
    Cleans up user after test finishes.
    """
    suffix = get_unique_suffix()
    email = f"razor_test_{suffix}@example.com"
    
    async with async_session_factory() as session:
        user = DBmodels.User(
            email=email,
            hashed_password="mock_password_hash",
            name="Razorpay Test User",
            role=DBmodels.UserRole.LEARNER,
            is_active=True
        )
        session.add(user)
        await session.flush()
        user_id = user.id
        await session.commit()

    payload = {
        "sub": str(user_id),
        "type": "access",
        "role": "learner",
        "token_version": 0
    }
    token = create_access_token(payload)
    headers = {"Authorization": f"Bearer {token}"}

    yield user_id, headers

    # Cleanup seeded data
    async with async_session_factory() as session:
        await session.execute(text("DELETE FROM subscriptions WHERE user_id = :uid"), {"uid": user_id})
        await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
        await session.commit()

@pytest.mark.asyncio
async def test_create_order_insufficient_amount(seed_user):
    user_id, headers = seed_user
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test that an amount less than 100 paise raises 400 Bad Request
        response = await client.post(
            "/api/create-order",
            json={"amount": 50, "currency": "INR"},
            headers=headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Amount must be at least 100 paise" in response.json()["detail"]

@pytest.mark.asyncio
@patch("razorpay.Client")
async def test_create_order_success(mock_razorpay_client, seed_user):
    user_id, headers = seed_user
    # Mock the Client and the order.create method
    mock_instance = MagicMock()
    mock_instance.order.create.return_value = {
        "id": "order_test123",
        "amount": 2900,
        "currency": "INR"
    }
    mock_razorpay_client.return_value = mock_instance

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/create-order",
            json={"amount": 2900, "currency": "INR", "receipt": "test_receipt"},
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["order_id"] == "order_test123"
        assert data["amount"] == 2900
        assert data["currency"] == "INR"
        mock_instance.order.create.assert_called_once()

@pytest.mark.asyncio
async def test_verify_payment_missing_fields(seed_user):
    user_id, headers = seed_user
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test missing fields returns 400
        response = await client.post(
            "/api/verify-payment",
            json={"razorpay_order_id": "order_123"},  # missing other fields
            headers=headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Missing fields" in response.json()["detail"]

@pytest.mark.asyncio
@patch("razorpay.Client")
async def test_verify_payment_signature_mismatch(mock_razorpay_client, seed_user):
    user_id, headers = seed_user
    # Mock verification signature verification failure
    mock_instance = MagicMock()
    mock_instance.utility.verify_payment_signature.side_effect = SignatureVerificationError("Mismatch")
    mock_razorpay_client.return_value = mock_instance

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/verify-payment",
            json={
                "razorpay_order_id": "order_123",
                "razorpay_payment_id": "pay_123",
                "razorpay_signature": "sig_wrong"
            },
            headers=headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Signature mismatch" in response.json()["detail"]

@pytest.mark.asyncio
@patch("razorpay.Client")
async def test_verify_payment_success(mock_razorpay_client, seed_user):
    user_id, headers = seed_user
    # Mock signature verification success
    mock_instance = MagicMock()
    mock_instance.utility.verify_payment_signature.return_value = True
    mock_razorpay_client.return_value = mock_instance

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/verify-payment",
            json={
                "razorpay_order_id": "order_123",
                "razorpay_payment_id": "pay_123",
                "razorpay_signature": "sig_valid"
            },
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"
        
        # Verify db updated subscription to PRO
        async with async_session_factory() as session:
            from sqlalchemy import select
            stmt = select(DBmodels.Subscription).where(DBmodels.Subscription.user_id == user_id)
            res = await session.execute(stmt)
            sub = res.scalar_one_or_none()
            assert sub is not None
            assert sub.plan == DBmodels.SubscriptionPlan.PRO
            assert sub.status == DBmodels.SubscriptionStatus.ACTIVE
