import os
import sys
import json
import pytest
import asyncio
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException, status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models as DBmodels
from core.database import async_session_factory
from main import app
import models_billing
import metering_middleware

def get_unique_suffix():
    return os.urandom(4).hex()

# -----------------------------------------------------------------------------
# 1. API Key Management Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
@patch("routers.developer.redis_client", new_callable=AsyncMock)
async def test_api_key_lifecycle(mock_redis):
    suffix = get_unique_suffix()
    email = f"dev_user_{suffix}@example.com"

    mock_redis.delete = AsyncMock(return_value=True)
    mock_redis.setex = AsyncMock(return_value=True)

    # 1. Register test user
    async with async_session_factory() as session:
        user = DBmodels.User(email=email, name="Developer User", hashed_password="pwd", is_active=True)
        session.add(user)
        await session.commit()
        user_id = user.id

    try:
        # Generate Access Token for Auth
        from core.auth import create_access_token
        access_token = create_access_token(user)

        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # A. Create a Key
            res = await client.post(
                "/api/v1/developer/keys", 
                json={"name": "Prod Server Key"},
                headers=headers
            )
            assert res.status_code == 200
            data = res.json()
            assert data["name"] == "Prod Server Key"
            assert "api_key" in data
            assert data["api_key"].startswith("qc_live_")
            assert data["is_active"] is True
            key_id = data["id"]
            
            # B. List Keys
            res = await client.get("/api/v1/developer/keys", headers=headers)
            assert res.status_code == 200
            keys_list = res.json()
            assert len(keys_list) >= 1
            assert any(k["id"] == key_id for k in keys_list)

            # C. Deactivate Key
            res = await client.patch(
                f"/api/v1/developer/keys/{key_id}",
                json={"is_active": False},
                headers=headers
            )
            assert res.status_code == 200
            assert res.json()["is_active"] is False

            # D. Delete Key
            res = await client.delete(f"/api/v1/developer/keys/{key_id}", headers=headers)
            assert res.status_code == 200
            assert res.json()["status"] == "success"

            # Check key is deleted in DB
            async with async_session_factory() as session:
                stmt = select(models_billing.ApiKey).where(models_billing.ApiKey.id == key_id)
                db_res = await session.execute(stmt)
                assert db_res.scalar_one_or_none() is None

    finally:
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM developer_api_keys WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            await session.commit()


# -----------------------------------------------------------------------------
# 2. Wallet & Top-up Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
@patch("routers.developer.redis_client", new_callable=AsyncMock)
async def test_wallet_operations(mock_redis):
    suffix = get_unique_suffix()
    email = f"wallet_user_{suffix}@example.com"

    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=True)

    async with async_session_factory() as session:
        user = DBmodels.User(email=email, name="Wallet User", hashed_password="pwd", is_active=True)
        session.add(user)
        await session.commit()
        user_id = user.id

    try:
        from core.auth import create_access_token
        access_token = create_access_token(user)

        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {access_token}"}

            # A. Get initial wallet
            res = await client.get("/api/v1/developer/wallet", headers=headers)
            assert res.status_code == 200
            assert res.json()["balance_credits"] == 0.0
            assert res.json()["auto_topup_enabled"] is False

            # B. Top-up Wallet
            res = await client.post(
                "/api/v1/developer/wallet/topup",
                json={"amount": 25.50},
                headers=headers
            )
            assert res.status_code == 200
            assert res.json()["balance_credits"] == 25.50

            # C. Update Auto-Topup Settings
            res = await client.patch(
                "/api/v1/developer/wallet",
                json={"auto_topup_enabled": True},
                headers=headers
            )
            assert res.status_code == 200
            assert res.json()["auto_topup_enabled"] is True

    finally:
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM wallet_balances WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            await session.commit()


# -----------------------------------------------------------------------------
# 3. Metering Middleware & Public Sim Route Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
@patch("metering_middleware.redis_client", new_callable=AsyncMock)
@patch("routers.public_circuit.QuantumEngine")
async def test_metering_middleware_simulation(mock_q_engine, mock_redis):
    suffix = get_unique_suffix()
    email = f"meter_user_{suffix}@example.com"
    raw_key = "qc_live_secretkey12345"
    hashed_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    # Mock Quantum Simulator run
    mock_sim_instance = MagicMock()
    mock_sim_instance.run_circuit_v1.return_value = {
        "type": "ideal",
        "probabilities": {"00": 1.0},
        "statevector": None,
        "metrics": {"depth": 1, "gate_count": {"h": 1}, "qubit_count": 1},
        "execution_time_ms": 12.5
    }
    mock_q_engine.return_value = mock_sim_instance

    # Mock Redis responses
    # Return 1 for token bucket EVAL script
    mock_redis.eval = AsyncMock(return_value=1)
    mock_redis.incrbyfloat = AsyncMock(return_value=15.50)
    mock_pipeline = MagicMock()
    mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
    mock_pipeline.__aexit__ = AsyncMock(return_value=None)
    mock_pipeline.execute = AsyncMock(return_value=True)
    mock_redis.pipeline = MagicMock(return_value=mock_pipeline)

    async with async_session_factory() as session:
        user = DBmodels.User(email=email, name="Meter User", hashed_password="pwd", is_active=True)
        session.add(user)
        await session.flush()
        
        api_key = models_billing.ApiKey(
            user_id=user.id,
            hashed_key=hashed_key,
            prefix="qc_live_",
            name="Test Key",
            is_active=True
        )
        wallet = models_billing.WalletBalance(user_id=user.id, balance_credits=20.0)
        session.add_all([api_key, wallet])
        await session.commit()
        user_id = user.id

    try:
        # Test A: Successful API Key simulation
        # Mock Redis get key info to simulate cache hit
        mock_redis.get = AsyncMock(side_effect=lambda k: {
            f"developer:apikey:{hashed_key}": json.dumps({
                "id": 1, "user_id": user_id, "prefix": "qc_live_", "name": "Test Key", "is_active": True
            }),
            f"developer:wallet_blocked:{user_id}": None,
            f"developer:wallet:{user_id}": "20.0"
        }.get(k))

        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"X-API-Key": raw_key}
            payload = {
                "num_qubits": 2,
                "shots": 1024,
                "gates": [
                    {"name": "h", "qubits": [0]}
                ]
            }
            res = await client.post("/api/v1/public/circuit/simulate", json=payload, headers=headers)
            assert res.status_code == 200
            assert res.json()["type"] == "ideal"
            
            # Check Redis decrement called for charge
            mock_redis.incrbyfloat.assert_called_with(f"developer:wallet:{user_id}", -0.015)

        # Test B: Deny request when API key is missing
        async with AsyncClient(app=app, base_url="http://test") as client:
            res = await client.post("/api/v1/public/circuit/simulate", json=payload)
            assert res.status_code == 401
            assert "X-API-Key header is missing" in res.json()["detail"]

        # Test C: Deny request when wallet blocked flag is set
        mock_redis.get = AsyncMock(side_effect=lambda k: {
            f"developer:apikey:{hashed_key}": json.dumps({
                "id": 1, "user_id": user_id, "prefix": "qc_live_", "name": "Test Key", "is_active": True
            }),
            f"developer:wallet_blocked:{user_id}": "1"
        }.get(k))

        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"X-API-Key": raw_key}
            res = await client.post("/api/v1/public/circuit/simulate", json=payload, headers=headers)
            assert res.status_code == 402
            assert "Insufficient funds" in res.json()["detail"]

    finally:
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM developer_api_keys WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM wallet_balances WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            await session.commit()


# -----------------------------------------------------------------------------
# 4. Background Sync Test
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
@patch("metering_middleware.redis_client", new_callable=AsyncMock)
async def test_background_metrics_flush(mock_redis):
    suffix = get_unique_suffix()
    email = f"flush_user_{suffix}@example.com"
    raw_key = "qc_live_flushkey"
    hashed_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    async with async_session_factory() as session:
        user = DBmodels.User(email=email, name="Flush User", hashed_password="pwd", is_active=True)
        session.add(user)
        await session.flush()
        
        api_key = models_billing.ApiKey(
            user_id=user.id,
            hashed_key=hashed_key,
            prefix="qc_live_",
            name="Flush Key",
            is_active=True
        )
        wallet = models_billing.WalletBalance(user_id=user.id, balance_credits=100.00)
        session.add_all([api_key, wallet])
        await session.commit()
        user_id = user.id
        api_key_id = api_key.id

    try:
        # Mock scan to return keys to flush
        mock_redis.scan = AsyncMock(side_effect=[
            (0, [f"developer:wallet:{user_id}"]), # first scan for wallets
            (0, [f"developer:usage:daily:{api_key_id}:2026-06-14"]) # second scan for usage
        ])
        
        mock_redis.get = AsyncMock(return_value="94.20") # simulated new wallet balance
        mock_redis.hgetall = AsyncMock(return_value={
            "requests": "15",
            "total_shots": "15360",
            "total_spend": "5.80"
        })

        # Run flush routine
        await metering_middleware.flush_cumulative_metrics_to_db()

        # Verify database is updated
        async with async_session_factory() as session:
            # Check Wallet
            stmt = select(models_billing.WalletBalance).where(models_billing.WalletBalance.user_id == user_id)
            res = await session.execute(stmt)
            db_wallet = res.scalar_one()
            assert float(db_wallet.balance_credits) == 94.20

            # Check Usage Rollup
            stmt = select(models_billing.DailyUsageRollup).where(
                models_billing.DailyUsageRollup.api_key_id == api_key_id,
                models_billing.DailyUsageRollup.usage_date == "2026-06-14"
            )
            res = await session.execute(stmt)
            db_rollup = res.scalar_one()
            assert db_rollup.requests_count == 15
            assert db_rollup.total_shots == 15360
            assert float(db_rollup.total_spend) == 5.80

    finally:
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM daily_usage_rollups WHERE api_key_id = :kid"), {"kid": api_key_id})
            await session.execute(text("DELETE FROM developer_api_keys WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM wallet_balances WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            await session.commit()
