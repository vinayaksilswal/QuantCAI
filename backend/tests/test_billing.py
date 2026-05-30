import os
import sys
import pytest
import stripe
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models as DBmodels
from core.database import async_session_factory, engine
from main import app  # imports main app with billing route registered

import billing

# Setup billing configurations for test mode
billing.STRIPE_API_KEY = "sk_test_mock"
billing.STRIPE_WEBHOOK_SECRET = "whsec_test_mock"



# -----------------------------------------------------------------------------
# Mocks & Helpers
# -----------------------------------------------------------------------------
class StripeDictMock(dict):
    """
    A dictionary subclass that allows dot-notation attribute access.
    Perfect for mocking Stripe API responses which support both dictionary
    access (.get) and attribute access (sub.id).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k, v in self.items():
            if isinstance(v, dict):
                self[k] = StripeDictMock(v)
            elif isinstance(v, list):
                self[k] = [StripeDictMock(i) if isinstance(i, dict) else i for i in v]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

def get_unique_suffix():
    return os.urandom(4).hex()

# -----------------------------------------------------------------------------
# 1. Feature Access Checks and Redis Caching Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
@patch("billing.redis_client", new_callable=AsyncMock)
async def test_check_feature_access(mock_redis):
    # Setup test database records
    suffix = get_unique_suffix()
    email_free = f"free_{suffix}@example.com"
    email_pro = f"pro_{suffix}@example.com"
    email_ent = f"ent_{suffix}@example.com"

    async with async_session_factory() as session:
        # Create users
        user_free = DBmodels.User(email=email_free, name="Free User", hashed_password="pwd", is_active=True)
        user_pro = DBmodels.User(email=email_pro, name="Pro User", hashed_password="pwd", is_active=True)
        user_ent = DBmodels.User(email=email_ent, name="Ent User", hashed_password="pwd", is_active=True)
        session.add_all([user_free, user_pro, user_ent])
        await session.flush()

        # Create subscriptions
        sub_free = DBmodels.Subscription(user_id=user_free.id, plan=DBmodels.SubscriptionPlan.FREE, status=DBmodels.SubscriptionStatus.ACTIVE)
        sub_pro = DBmodels.Subscription(user_id=user_pro.id, plan=DBmodels.SubscriptionPlan.PRO, status=DBmodels.SubscriptionStatus.ACTIVE)
        sub_ent = DBmodels.Subscription(user_id=user_ent.id, plan=DBmodels.SubscriptionPlan.ENTERPRISE, status=DBmodels.SubscriptionStatus.ACTIVE)
        session.add_all([sub_free, sub_pro, sub_ent])
        await session.commit()

        user_free_id = user_free.id
        user_pro_id = user_pro.id
        user_ent_id = user_ent.id

    try:
        # Refetch users inside active sessions or pass a clean copy
        async with async_session_factory() as session:
            stmt = select(DBmodels.User).where(DBmodels.User.id == user_free_id)
            res = await session.execute(stmt)
            db_user_free = res.scalar_one()

            stmt = select(DBmodels.User).where(DBmodels.User.id == user_pro_id)
            res = await session.execute(stmt)
            db_user_pro = res.scalar_one()

            stmt = select(DBmodels.User).where(DBmodels.User.id == user_ent_id)
            res = await session.execute(stmt)
            db_user_ent = res.scalar_one()

            # Test A: FREE Tier Capabilities
            # Expected: ai_tutor_pro=False, pqc_scan=True, api_access=True, cbom_export=False
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.setex = AsyncMock(return_value=True)

            assert await billing.check_feature_access(db_user_free, "ai_tutor_pro", session) is False
            assert await billing.check_feature_access(db_user_free, "pqc_scan", session) is True
            assert await billing.check_feature_access(db_user_free, "api_access", session) is True
            assert await billing.check_feature_access(db_user_free, "cbom_export", session) is False

            # Cache check for free user: verify setex called with key
            mock_redis.setex.assert_any_call(f"feature_access:{user_free_id}:ai_tutor_pro", 60, "false")
            mock_redis.setex.assert_any_call(f"feature_access:{user_free_id}:pqc_scan", 60, "true")

            # Test B: PRO Tier Capabilities
            # Expected: ai_tutor_pro=True, pqc_scan=True, api_access=True, cbom_export=False
            assert await billing.check_feature_access(db_user_pro, "ai_tutor_pro", session) is True
            assert await billing.check_feature_access(db_user_pro, "pqc_scan", session) is True
            assert await billing.check_feature_access(db_user_pro, "api_access", session) is True
            assert await billing.check_feature_access(db_user_pro, "cbom_export", session) is False

            # Test C: ENTERPRISE Tier Capabilities
            # Expected: ai_tutor_pro=True, pqc_scan=True, api_access=True, cbom_export=True
            assert await billing.check_feature_access(db_user_ent, "ai_tutor_pro", session) is True
            assert await billing.check_feature_access(db_user_ent, "pqc_scan", session) is True
            assert await billing.check_feature_access(db_user_ent, "api_access", session) is True
            assert await billing.check_feature_access(db_user_ent, "cbom_export", session) is True

            # Test D: Cache Hit (Redis returns value, DB not queried)
            mock_redis.get = AsyncMock(return_value="true")
            # Query without db session to verify it uses cached response if active
            assert await billing.check_feature_access(db_user_free, "ai_tutor_pro", None) is True
            mock_redis.get.assert_called_with(f"feature_access:{user_free_id}:ai_tutor_pro")

    finally:
        # Cleanup test data
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM subscriptions WHERE user_id IN (:u1, :u2, :u3)"), {"u1": user_free_id, "u2": user_pro_id, "u3": user_ent_id})
            await session.execute(text("DELETE FROM users WHERE id IN (:u1, :u2, :u3)"), {"u1": user_free_id, "u2": user_pro_id, "u3": user_ent_id})
            await session.commit()

# -----------------------------------------------------------------------------
# 2. Checkout Session and Customer Portal Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
@patch("stripe.Customer.list")
@patch("stripe.Customer.create")
@patch("stripe.checkout.Session.create")
async def test_create_checkout_session(mock_checkout_create, mock_cust_create, mock_cust_list):
    suffix = get_unique_suffix()
    email = f"billing_chk_{suffix}@example.com"

    # Setup stripe mocks
    mock_cust_list.return_value = StripeDictMock(data=[])
    mock_cust_create.return_value = StripeDictMock(id="cus_new123")
    mock_checkout_create.return_value = StripeDictMock(url="https://checkout.stripe.com/pay/cs_test_123")

    async with async_session_factory() as session:
        user = DBmodels.User(email=email, name="Checkout User", hashed_password="pwd", is_active=True)
        session.add(user)
        await session.commit()
        user_id = user.id

    try:
        async with async_session_factory() as session:
            stmt = select(DBmodels.User).where(DBmodels.User.id == user_id)
            res = await session.execute(stmt)
            db_user = res.scalar_one()

            # Test checkout creation
            checkout_url = await billing.create_checkout_session(db_user, "pro", session)
            assert checkout_url == "https://checkout.stripe.com/pay/cs_test_123"

            # Check that stripe customer create was called and stripe_customer_id updated in DB
            mock_cust_create.assert_called_once_with(
                email=email,
                name="Checkout User",
                metadata={"user_id": str(user_id)}
            )
            
            # Refresh user and check stripe_customer_id
            await session.refresh(db_user)
            assert db_user.stripe_customer_id == "cus_new123"

            # Check checkout session parameters
            mock_checkout_create.assert_called_once()
            args, kwargs = mock_checkout_create.call_args
            assert kwargs["customer"] == "cus_new123"
            assert kwargs["metadata"]["plan"] == "pro"
            assert kwargs["metadata"]["user_id"] == str(user_id)

    finally:
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            await session.commit()

@pytest.mark.asyncio
@patch("stripe.billing_portal.Session.create")
async def test_create_customer_portal_session(mock_portal_create):
    mock_portal_create.return_value = StripeDictMock(url="https://billing.stripe.com/p/session/portal_123")
    
    # 1. Missing Customer ID raises HTTP 400
    user_no_cust = DBmodels.User(email="test@example.com", name="Test", stripe_customer_id=None)
    with pytest.raises(HTTPException) as exc:
        await billing.create_customer_portal_session(user_no_cust)
    assert exc.value.status_code == 400

    # 2. Valid customer ID returns portal session URL
    user_with_cust = DBmodels.User(email="test@example.com", name="Test", stripe_customer_id="cus_active999")
    portal_url = await billing.create_customer_portal_session(user_with_cust)
    assert portal_url == "https://billing.stripe.com/p/session/portal_123"
    mock_portal_create.assert_called_once_with(
        customer="cus_active999",
        return_url=mock_portal_create.call_args[1]["return_url"]
    )

# -----------------------------------------------------------------------------
# 3. Webhook signature validation endpoint test
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
@patch("stripe.Webhook.construct_event")
async def test_webhook_handler_endpoint_validation(mock_construct_event):
    async with AsyncClient(app=app, base_url="http://test") as client:
        # A. Missing signature returns 400
        res = await client.post("/billing/webhook", content="{}")
        assert res.status_code == 400
        assert "stripe-signature header is missing" in res.json()["detail"]

        # B. Invalid signature/payload returns 400
        mock_construct_event.side_effect = stripe.error.SignatureVerificationError("Invalid signature", "sig_header")
        res = await client.post("/billing/webhook", content="{}", headers={"stripe-signature": "invalid_sig"})
        assert res.status_code == 400
        assert "Invalid signature" in res.json()["detail"]

        # C. Valid signature returns 200 immediately
        mock_construct_event.side_effect = None
        mock_construct_event.return_value = {"type": "checkout.session.completed", "id": "evt_123"}
        res = await client.post("/billing/webhook", content="{}", headers={"stripe-signature": "valid_sig"})
        assert res.status_code == 200
        assert res.json() == {"status": "event_received"}

# -----------------------------------------------------------------------------
# 4. Webhook Events Handling Tests (Database & Cache Invalidation)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
@patch("stripe.Subscription.retrieve")
@patch("billing.redis_client", new_callable=AsyncMock)
async def test_webhook_event_handlers(mock_redis, mock_sub_retrieve):
    suffix = get_unique_suffix()
    email = f"webhook_event_{suffix}@example.com"
    customer_id = f"cus_webhook_{suffix}"
    sub_id = f"sub_webhook_{suffix}"

    mock_redis.delete = AsyncMock(return_value=True)

    async with async_session_factory() as session:
        # Seed user
        user = DBmodels.User(email=email, name="Webhook User", stripe_customer_id=customer_id, hashed_password="pwd", is_active=True)
        session.add(user)
        await session.commit()
        user_id = user.id

    try:
        # Mock retrieval of Stripe subscription details
        stripe_sub_mock = {
            "id": sub_id,
            "customer": customer_id,
            "status": "active",
            "current_period_end": 1893456000,  # Year 2030
            "items": {
                "data": [{
                    "price": {"id": "price_pro_default"}
                }]
            }
        }
        mock_sub_retrieve.return_value = StripeDictMock(stripe_sub_mock)

        # ----------------------------------------
        # Test 1: checkout.session.completed
        # ----------------------------------------
        checkout_session_data = {
            "customer": customer_id,
            "subscription": sub_id,
            "metadata": {
                "user_id": str(user_id),
                "plan": "pro"
            }
        }
        await billing.handle_checkout_session_completed(checkout_session_data)

        # Assert database updates
        async with async_session_factory() as session:
            stmt = select(DBmodels.Subscription).where(DBmodels.Subscription.user_id == user_id)
            res = await session.execute(stmt)
            db_sub = res.scalar_one()

            assert db_sub.stripe_subscription_id == sub_id
            assert db_sub.status == DBmodels.SubscriptionStatus.ACTIVE
            assert db_sub.plan == DBmodels.SubscriptionPlan.PRO
            assert db_sub.current_period_end is not None

        # Assert Redis cache cleared
        mock_redis.delete.assert_called()

        # ----------------------------------------
        # Test 2: customer.subscription.updated (upgrade/tier change)
        # ----------------------------------------
        mock_redis.delete.reset_mock()
        # Mock Stripe sending subscription update with Enterprise price
        subscription_updated_data = {
            "id": sub_id,
            "customer": customer_id,
            "status": "active",
            "current_period_end": 1893456000,
            "items": {
                "data": [{
                    "price": {"id": "price_enterprise_default"}
                }]
            }
        }
        await billing.handle_subscription_updated(subscription_updated_data)

        # Assert database has updated plan to Enterprise
        async with async_session_factory() as session:
            stmt = select(DBmodels.Subscription).where(DBmodels.Subscription.stripe_subscription_id == sub_id)
            res = await session.execute(stmt)
            db_sub = res.scalar_one()

            assert db_sub.plan == DBmodels.SubscriptionPlan.ENTERPRISE
            assert db_sub.status == DBmodels.SubscriptionStatus.ACTIVE

        # Assert Redis cache cleared
        mock_redis.delete.assert_called()

        # ----------------------------------------
        # Test 3: invoice.payment_failed (status past_due)
        # ----------------------------------------
        mock_redis.delete.reset_mock()
        invoice_failed_data = {
            "id": "in_failed_123",
            "customer": customer_id,
            "subscription": sub_id
        }
        
        with patch("billing.send_payment_failed_email", new_callable=AsyncMock) as mock_send_email:
            await billing.handle_invoice_payment_failed(invoice_failed_data)
            
            # Assert subscription marked past_due in DB
            async with async_session_factory() as session:
                stmt = select(DBmodels.Subscription).where(DBmodels.Subscription.stripe_subscription_id == sub_id)
                res = await session.execute(stmt)
                db_sub = res.scalar_one()

                assert db_sub.status == DBmodels.SubscriptionStatus.PAST_DUE

            # Assert email alert sent
            mock_send_email.assert_called_once_with(email, "in_failed_123")

        # ----------------------------------------
        # Test 4: customer.subscription.deleted (cancel & downgrade to free)
        # ----------------------------------------
        mock_redis.delete.reset_mock()
        subscription_deleted_data = {
            "id": sub_id,
            "customer": customer_id,
            "status": "canceled"
        }
        await billing.handle_subscription_deleted(subscription_deleted_data)

        # Assert database shows subscription cancelled and plan set to free
        async with async_session_factory() as session:
            stmt = select(DBmodels.Subscription).where(DBmodels.Subscription.stripe_subscription_id == sub_id)
            res = await session.execute(stmt)
            db_sub = res.scalar_one()

            assert db_sub.status == DBmodels.SubscriptionStatus.CANCELLED
            assert db_sub.plan == DBmodels.SubscriptionPlan.FREE

        # Assert Redis cache cleared
        mock_redis.delete.assert_called()

    finally:
        # Cleanup
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM subscriptions WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            await session.commit()
