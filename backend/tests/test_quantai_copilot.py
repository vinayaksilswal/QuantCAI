import os
import sys
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, select

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models as DBmodels
from core.database import async_session_factory
from main import app
from security import create_access_token, hash_api_key

def get_unique_suffix():
    return os.urandom(4).hex()

class MockChatChunk:
    def __init__(self, content):
        self.content = content

async def mock_astream(*args, **kwargs):
    yield MockChatChunk("Mocked agent ")
    yield MockChatChunk("response chunk.")

@pytest.mark.asyncio
@patch("routers.quantai.redis_client", new_callable=AsyncMock)
@patch("routers.quantai.llm_with_tools", new_callable=AsyncMock)
async def test_quantai_copilot_auth_and_billing(mock_llm, mock_redis):
    # Mock LLM stream
    mock_llm.astream = MagicMock(side_effect=mock_astream)

    suffix = get_unique_suffix()
    email = f"quantai_user_{suffix}@example.com"
    api_key_plaintext = f"qcai_test_key_{suffix}"
    hashed_key = hash_api_key(api_key_plaintext)

    async with async_session_factory() as session:
        # Create user
        user = DBmodels.User(
            email=email,
            hashed_password="mock_password_hash",
            name="QuantAI Test User",
            role=DBmodels.UserRole.DEVELOPER,
            is_active=True
        )
        session.add(user)
        await session.flush()
        user_id = user.id

        # Create Developer API Key
        api_key = DBmodels.APIKey(
            user_id=user_id,
            key_hash=hashed_key,
            label="QuantAI Copilot Test Key",
            tier=DBmodels.APIKeyTier.PRO,
            daily_limit=1000,
            requests_today=0,
            is_active=True
        )
        session.add(api_key)

        # Create wallet
        wallet = DBmodels.WalletBalance(
            user_id=user_id,
            balance_credits=10.0
        )
        session.add(wallet)
        await session.commit()

    try:
        # 1. Test standard JWT token auth
        payload = {
            "sub": str(user_id),
            "type": "access",
            "role": "developer",
            "token_version": 0
        }
        token = create_access_token(payload)

        # Redis mock configuration
        mock_redis.get.side_effect = lambda k: {
            f"developer:wallet:{user_id}": "10.0",
            f"quantai_history:conv-1": None
        }.get(k)
        mock_redis.incrbyfloat.return_value = 9.997
        mock_redis.setex.return_value = True

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # POST with JWT Token
            headers = {"Authorization": f"Bearer {token}"}
            res = await client.post(
                "/api/v1/quantai/chat",
                headers=headers,
                json={
                    "message": "Hello Copilot",
                    "conversation_id": "conv-1",
                    "context": "learn",
                    "client_context": {"module_id": "mod-1", "chapter_title": "Chapter 1"}
                }
            )
            assert res.status_code == 200
            # SSE streams return text/event-stream
            assert "text/event-stream" in res.headers["content-type"]
            body = res.text
            assert "conv-1" in body
            assert "Mocked agent " in body
            assert "response chunk." in body
            
            # Verify atomic decrement was called
            mock_redis.incrbyfloat.assert_called_with(f"developer:wallet:{user_id}", -0.003)

        # 2. Test programmatic X-API-Key auth
        mock_redis.incrbyfloat.reset_mock()
        # Mock API Key caching lookup in Redis (metering_middleware.py)
        api_key_cache_key = f"developer:apikey:{hashed_key}"
        key_info = {
            "id": 1,
            "user_id": user_id,
            "prefix": "qcai_test",
            "name": "QuantAI Copilot Test Key",
            "is_active": True
        }
        
        mock_redis.get.side_effect = lambda k: {
            api_key_cache_key: json.dumps(key_info),
            f"developer:wallet:{user_id}": "5.0",
            f"quantai_history:conv-2": None,
            f"developer:wallet_blocked:{user_id}": "0"
        }.get(k)
        
        # token bucket Lua eval success return
        mock_redis.eval.return_value = 1
        mock_redis.incrbyfloat.return_value = 4.997

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"X-API-Key": api_key_plaintext}
            res = await client.post(
                "/api/v1/quantai/chat",
                headers=headers,
                json={
                    "message": "Check circuit compilation",
                    "conversation_id": "conv-2",
                    "context": "circuit-builder",
                    "client_context": {"placed_gates_count": 5}
                }
            )
            assert res.status_code == 200
            assert "Mocked agent " in res.text
            assert "response chunk." in res.text
            mock_redis.incrbyfloat.assert_called_with(f"developer:wallet:{user_id}", -0.003)

        # 3. Test HTTP 402 blocking when credit balance is empty
        mock_redis.get.side_effect = lambda k: {
            f"developer:wallet:{user_id}": "0.00",
            f"developer:wallet_blocked:{user_id}": "1"
        }.get(k)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token}"}
            res = await client.post(
                "/api/v1/quantai/chat",
                headers=headers,
                json={
                    "message": "This should be blocked",
                    "conversation_id": "conv-3",
                    "context": "learn"
                }
            )
            assert res.status_code == 402
            assert "Insufficient funds" in res.json()["detail"]

    finally:
        # DB cleanup
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM wallet_balances WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM api_keys WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            await session.commit()


@pytest.mark.asyncio
@patch("routers.quantai.redis_client", new_callable=AsyncMock)
@patch("routers.quantai.llm_with_tools", new_callable=AsyncMock)
async def test_quantai_copilot_multi_agent_routing(mock_llm, mock_redis):
    # Mock LLM stream
    mock_llm.astream = MagicMock(side_effect=mock_astream)

    suffix = get_unique_suffix()
    email = f"routing_user_{suffix}@example.com"

    async with async_session_factory() as session:
        user = DBmodels.User(
            email=email,
            hashed_password="mock_password_hash",
            name="Routing User",
            role=DBmodels.UserRole.LEARNER,
            is_active=True
        )
        session.add(user)
        await session.flush()
        user_id = user.id

        wallet = DBmodels.WalletBalance(
            user_id=user_id,
            balance_credits=10.0
        )
        session.add(wallet)
        await session.commit()

    try:
        payload = {
            "sub": str(user_id),
            "type": "access",
            "role": "learner",
            "token_version": 0
        }
        token = create_access_token(payload)

        mock_redis.get.side_effect = lambda k: {
            f"developer:wallet:{user_id}": "10.0",
            f"quantai_history:conv-router": None
        }.get(k)
        mock_redis.incrbyfloat.return_value = 9.997
        mock_redis.setex.return_value = True

        contexts = ["learn", "circuit-builder", "pqc-scanner"]
        expected_prompts_keywords = ["Pedagogical", "Compilation", "Offensive"]

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for ctx, kw in zip(contexts, expected_prompts_keywords):
                res = await client.post(
                    "/api/v1/quantai/chat",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "message": "Query for routing",
                        "conversation_id": "conv-router",
                        "context": ctx
                    }
                )
                assert res.status_code == 200
                
                # Retrieve the arguments passed to mock_llm.astream
                args, kwargs = mock_llm.astream.call_args
                system_message = args[0][0]
                assert system_message.type == "system"
                assert kw in system_message.content

    finally:
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM wallet_balances WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            await session.commit()
