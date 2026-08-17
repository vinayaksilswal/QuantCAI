import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from datetime import datetime, timezone
import hashlib
import json
import urllib.parse
from core.config import settings
import models as DBmodels

@pytest.mark.asyncio
async def test_warriorplus_ipn_subscription_upgrade(free_user, mock_redis):
    """Test WarriorPlus IPN successfully upgrades a user to PRO."""
    # Ensure security key is set
    settings.WARRIORPLUS_SECURITY_KEY = "test-secret-key"
    settings.WARRIORPLUS_PRO_PRODUCT_ID = "PRO_TEST_123"
    
    # Construct a valid IPN payload
    payload = {
        "WP_ACTION": "sale",
        "WP_BUYER_EMAIL": free_user.email,
        "WP_BUYER_NAME": "Free User",
        "WP_ITEM_NAME": "QuantCAI Pro",
        "WP_ITEM_NUMBER": "PRO_TEST_123",
        "WP_SALEID": "SALE_12345",
        "WP_TXNID": "TXN_12345",
        "WP_SECURITYKEY": "test-secret-key",
    }
    
    # URL encode payload like application/x-www-form-urlencoded
    data = urllib.parse.urlencode(payload)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/payment/warriorplus/ipn",
            content=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # WP IPN always expects 200 OK
        assert res.status_code == 200
        
        # Verify idempotency key was set
        assert await mock_redis.get("wp_ipn:SALE_12345:sale") is not None
        
        # Verify user tier was upgraded
        from core.database import async_session_factory
        from sqlalchemy import select
        from models import User, Subscription
        
        async with async_session_factory() as session:
            result = await session.execute(select(Subscription).where(Subscription.user_id == free_user.id))
            sub = result.scalars().first()
            assert sub is not None
            assert sub.plan == DBmodels.SubscriptionPlan.PRO
            assert sub.status == DBmodels.SubscriptionStatus.ACTIVE
            
            # The tier of the user should be pro
            user_result = await session.execute(select(User).where(User.id == free_user.id))
            updated_user = user_result.scalars().first()
            assert updated_user.role == DBmodels.UserRole.LEARNER  # Role is unchanged; the subscription drives tier
            
            # Testing idempotency - sending same request again
            res2 = await client.post(
                "/api/payment/warriorplus/ipn",
                content=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            assert res2.status_code == 200
            # The replay is acknowledged rather than reprocessed.
            assert "already processed" in res2.text.lower()
