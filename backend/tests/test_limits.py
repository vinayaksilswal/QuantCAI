import os
import sys
import pytest
import json
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, select

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models as DBmodels
from core.database import async_session_factory
from main import app
from security import create_access_token

def get_unique_suffix():
    return os.urandom(4).hex()

class MockChatChunk:
    def __init__(self, content):
        self.content = content

async def mock_astream(*args, **kwargs):
    yield MockChatChunk("Mocked agent response chunk.")

# Helper to create user, plan, usage, and wallet balance
async def create_test_user_with_plan(email: str, tier: DBmodels.Tier) -> int:
    async with async_session_factory() as session:
        user = DBmodels.User(
            email=email,
            hashed_password="mock_password_hash",
            name="Limits Test User",
            role=DBmodels.UserRole.LEARNER if tier != DBmodels.Tier.ENTERPRISE else DBmodels.UserRole.ENTERPRISE_USER,
            is_active=True
        )
        session.add(user)
        await session.flush()
        user_id = user.id

        plan = DBmodels.UserPlan(
            user_id=user_id,
            tier=tier,
            cycle_reset_date=date.today() + timedelta(days=30)
        )
        session.add(plan)

        usage = DBmodels.FeatureUsage(
            user_id=user_id,
            daily_ai_chats=0,
            monthly_pqc_scans=0,
            total_compute_overhead=0.0
        )
        session.add(usage)

        wallet = DBmodels.WalletBalance(
            user_id=user_id,
            balance_credits=10.0
        )
        session.add(wallet)
        await session.commit()
        return user_id

async def cleanup_test_user(user_id: int):
    async with async_session_factory() as session:
        await session.execute(text("DELETE FROM wallet_balances WHERE user_id = :uid"), {"uid": user_id})
        await session.execute(text("DELETE FROM feature_usages WHERE user_id = :uid"), {"uid": user_id})
        await session.execute(text("DELETE FROM user_plans WHERE user_id = :uid"), {"uid": user_id})
        await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
        await session.commit()

@pytest.mark.asyncio
async def test_free_user_simulation_limits():
    suffix = get_unique_suffix()
    email = f"free_sim_{suffix}@example.com"
    user_id = await create_test_user_with_plan(email, DBmodels.Tier.FREE)
    token = create_access_token({"sub": str(user_id), "type": "access", "role": "learner", "token_version": 0})
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Test Qubits Limit (> 5 qubits)
            res = await client.post(
                "/api/v1/simulator/execute",
                headers=headers,
                json={
                    "qasm_string": "OPENQASM 3.0;\ninclude \"stdgates.inc\";\nqubit[6] q;\nh q[0];\ncx q[0], q[1];",
                    "shots": 100,
                    "backend_choice": "Local AerSimulator",
                    "noise_model": "Ideal"
                }
            )
            assert res.status_code == 402
            assert res.json()["detail"]["error"] == "QUBIT_LIMIT_EXCEEDED"

            # 2. Test Depth Limit (> 15 gates depth)
            # 17 consecutive x gates
            res = await client.post(
                "/api/v1/simulator/execute",
                headers=headers,
                json={
                    "qasm_string": "OPENQASM 3.0;\ninclude \"stdgates.inc\";\nqubit[2] q;\nx q[0];\nx q[0];\nx q[0];\nx q[0];\nx q[0];\nx q[0];\nx q[0];\nx q[0];\nx q[0];\nx q[0];\nx q[0];\nx q[0];\nx q[0];\nx q[0];\nx q[0];\nx q[0];\nx q[0];",
                    "shots": 100,
                    "backend_choice": "Local AerSimulator",
                    "noise_model": "Ideal"
                }
            )
            assert res.status_code == 402
            assert res.json()["detail"]["error"] == "DEPTH_LIMIT_EXCEEDED"

            # 3. Test Shots Limit (> 1024 shots)
            res = await client.post(
                "/api/v1/simulator/execute",
                headers=headers,
                json={
                    "qasm_string": "OPENQASM 3.0;\ninclude \"stdgates.inc\";\nqubit[2] q;\nh q[0];",
                    "shots": 1025,
                    "backend_choice": "Local AerSimulator",
                    "noise_model": "Ideal"
                }
            )
            assert res.status_code == 402
            assert res.json()["detail"]["error"] == "SHOTS_LIMIT_EXCEEDED"

            # 4. Test Noise Model Restricted (e.g., Depolarizing)
            res = await client.post(
                "/api/v1/simulator/execute",
                headers=headers,
                json={
                    "qasm_string": "OPENQASM 3.0;\ninclude \"stdgates.inc\";\nqubit[2] q;\nh q[0];",
                    "shots": 100,
                    "backend_choice": "Local AerSimulator",
                    "noise_model": "Depolarizing"
                }
            )
            assert res.status_code == 402
            assert res.json()["detail"]["error"] == "NOISE_MODEL_RESTRICTED"

            # 5. Success case within Free limits (Ideal noise, qubits=2, depth=1, shots=100)
            res = await client.post(
                "/api/v1/simulator/execute",
                headers=headers,
                json={
                    "qasm_string": "OPENQASM 3.0;\ninclude \"stdgates.inc\";\nqubit[2] q;\nh q[0];",
                    "shots": 100,
                    "backend_choice": "Local AerSimulator",
                    "noise_model": "Ideal"
                }
            )
            assert res.status_code == 200

    finally:
        await cleanup_test_user(user_id)

@pytest.mark.asyncio
async def test_pro_user_simulation_limits():
    suffix = get_unique_suffix()
    email = f"pro_sim_{suffix}@example.com"
    user_id = await create_test_user_with_plan(email, DBmodels.Tier.PRO)
    token = create_access_token({"sub": str(user_id), "type": "access", "role": "learner", "token_version": 0})
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Qubits limit (> 30 qubits)
            res = await client.post(
                "/api/v1/simulator/execute",
                headers=headers,
                json={
                    "qasm_string": "OPENQASM 3.0;\ninclude \"stdgates.inc\";\nqubit[31] q;\nh q[0];",
                    "shots": 100,
                    "backend_choice": "Local AerSimulator",
                    "noise_model": "Ideal"
                }
            )
            assert res.status_code == 402
            assert res.json()["detail"]["error"] == "QUBIT_LIMIT_EXCEEDED"

            # 2. Shots limit (> 65,536 shots)
            res = await client.post(
                "/api/v1/simulator/execute",
                headers=headers,
                json={
                    "qasm_string": "OPENQASM 3.0;\ninclude \"stdgates.inc\";\nqubit[2] q;\nh q[0];",
                    "shots": 65537,
                    "backend_choice": "Local AerSimulator",
                    "noise_model": "Ideal"
                }
            )
            assert res.status_code == 402
            assert res.json()["detail"]["error"] == "SHOTS_LIMIT_EXCEEDED"

            # 3. Unlimited depth and advanced noise model should succeed (qubits <= 30, shots <= 65536)
            res = await client.post(
                "/api/v1/simulator/execute",
                headers=headers,
                json={
                    "qasm_string": "OPENQASM 3.0;\ninclude \"stdgates.inc\";\nqubit[2] q;\nh q[0];",
                    "shots": 100,
                    "backend_choice": "Local AerSimulator",
                    "noise_model": "Depolarizing"
                }
            )
            assert res.status_code == 200

    finally:
        await cleanup_test_user(user_id)

@pytest.mark.asyncio
@patch("routers.pqc.redis_client", new_callable=AsyncMock)
@patch("routers.pqc.scanner_engine.scan_tls_pqc")
async def test_pqc_scanning_limits(mock_scan, mock_redis):
    # Configure mock scan response with all required fields of ScanResponse
    mock_scan.return_value = {
        "domain": "example.com",
        "port": 443,
        "scan_timestamp": "2026-06-13T19:40:00Z",
        "scan_duration_ms": 150,
        "overall_risk_score": 10.0,
        "risk_level": "LOW",
        "hndl_risk_level": "LOW",
        "quantum_risk_grade": "Grade A",
        "tls_details": {
            "version": "TLSv1.3",
            "cipher_suite": "TLS_AES_256_GCM_SHA384",
            "key_exchange": "ECDHE",
            "key_exchange_group": "X25519",
            "key_exchange_bits": 256,
            "quantum_safe": False
        },
        "certificates": [],
        "findings": [],
        "cbom_summary": {
            "total_assets": 0,
            "vulnerable_assets": 0,
            "compliant_assets": 0,
            "pqc_readiness_pct": 100.0
        }
    }
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True

    suffix = get_unique_suffix()
    email_free = f"free_pqc_{suffix}@example.com"
    email_pro = f"pro_pqc_{suffix}@example.com"
    email_ent = f"ent_pqc_{suffix}@example.com"

    free_id = await create_test_user_with_plan(email_free, DBmodels.Tier.FREE)
    pro_id = await create_test_user_with_plan(email_pro, DBmodels.Tier.PRO)
    ent_id = await create_test_user_with_plan(email_ent, DBmodels.Tier.ENTERPRISE)

    token_free = create_access_token({"sub": str(free_id), "type": "access", "role": "learner", "token_version": 0})
    token_pro = create_access_token({"sub": str(pro_id), "type": "access", "role": "learner", "token_version": 0})
    token_ent = create_access_token({"sub": str(ent_id), "type": "access", "role": "enterprise_user", "token_version": 0})

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. FREE/PRO users should be blocked from scanning internal domains
            for token in (token_free, token_pro):
                res = await client.post(
                    "/api/v1/pqc/scan",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"domain": "127.0.0.1"}
                )
                assert res.status_code == 402
                assert res.json()["detail"]["error"] == "ENTERPRISE_REQUIRED"

            # 2. ENTERPRISE user should be allowed to scan internal domains
            res = await client.post(
                "/api/v1/pqc/scan",
                headers={"Authorization": f"Bearer {token_ent}"},
                json={"domain": "127.0.0.1"}
            )
            assert res.status_code == 200

            # 3. Monthly scan limits check:
            # For Free user, if they have monthly_pqc_scans >= 5, they should be blocked.
            async with async_session_factory() as session:
                stmt = select(DBmodels.FeatureUsage).where(DBmodels.FeatureUsage.user_id == free_id)
                db_res = await session.execute(stmt)
                usage = db_res.scalar_one()
                usage.monthly_pqc_scans = 5
                await session.commit()

            res = await client.post(
                "/api/v1/pqc/scan",
                headers={"Authorization": f"Bearer {token_free}"},
                json={"domain": "google.com"}
            )
            assert res.status_code == 402
            assert res.json()["detail"]["error"] == "PQC_LIMIT_EXCEEDED"

            # For Pro user, if they have monthly_pqc_scans >= 100, they should be blocked.
            async with async_session_factory() as session:
                stmt = select(DBmodels.FeatureUsage).where(DBmodels.FeatureUsage.user_id == pro_id)
                db_res = await session.execute(stmt)
                usage = db_res.scalar_one()
                usage.monthly_pqc_scans = 100
                await session.commit()

            res = await client.post(
                "/api/v1/pqc/scan",
                headers={"Authorization": f"Bearer {token_pro}"},
                json={"domain": "google.com"}
            )
            assert res.status_code == 402
            assert res.json()["detail"]["error"] == "PQC_LIMIT_EXCEEDED"

    finally:
        await cleanup_test_user(free_id)
        await cleanup_test_user(pro_id)
        await cleanup_test_user(ent_id)

@pytest.mark.asyncio
@patch("tier_limits.redis_client", new_callable=AsyncMock)
@patch("routers.quantai.redis_client", new_callable=AsyncMock)
@patch("routers.quantai.llm", new_callable=AsyncMock)
async def test_quantai_rate_limits_and_context_injection(mock_llm, mock_redis_quantai, mock_redis_tier):
    mock_llm.astream = MagicMock(side_effect=mock_astream)

    suffix = get_unique_suffix()
    email_free = f"free_ai_{suffix}@example.com"
    email_pro = f"pro_ai_{suffix}@example.com"

    free_id = await create_test_user_with_plan(email_free, DBmodels.Tier.FREE)
    pro_id = await create_test_user_with_plan(email_pro, DBmodels.Tier.PRO)

    token_free = create_access_token({"sub": str(free_id), "type": "access", "role": "learner", "token_version": 0})
    token_pro = create_access_token({"sub": str(pro_id), "type": "access", "role": "learner", "token_version": 0})

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Mock wallet balance retrieve in Redis
            wallet_free_key = f"developer:wallet:{free_id}"
            wallet_pro_key = f"developer:wallet:{pro_id}"

            # 1. Daily rate-limiting for FREE user: 11th chat blocked
            # Mock chats count key = "user:<id>:ai_chats:count"
            redis_chats_free_key = f"user:{free_id}:ai_chats:count"
            
            # Setup gets on both mocks
            for mock_r in (mock_redis_tier, mock_redis_quantai):
                mock_r.get.side_effect = lambda k: {
                    wallet_free_key: "10.0",
                    redis_chats_free_key: "10"
                }.get(k)
                mock_r.incrbyfloat.return_value = 9.997

            res = await client.post(
                "/api/v1/quantai/chat",
                headers={"Authorization": f"Bearer {token_free}"},
                json={
                    "message": "Hello 11th time!",
                    "context": "learn"
                }
            )
            assert res.status_code == 429
            assert res.json()["detail"]["error"] == "AI_LIMIT_EXCEEDED"

            # 2. Daily rate-limiting for PRO user: 11th chat allowed (unlimited)
            redis_chats_pro_key = f"user:{pro_id}:ai_chats:count"
            for mock_r in (mock_redis_tier, mock_redis_quantai):
                mock_r.get.side_effect = lambda k: {
                    wallet_pro_key: "10.0",
                    redis_chats_pro_key: "15"
                }.get(k)
                mock_r.incrbyfloat.return_value = 9.997

            res = await client.post(
                "/api/v1/quantai/chat",
                headers={"Authorization": f"Bearer {token_pro}"},
                json={
                    "message": "Hello PRO 16th time!",
                    "context": "learn"
                }
            )
            assert res.status_code == 200

            # 3. Context injection checks:
            # FREE tier: prompt blind to active workspace state (client_context stripped)
            for mock_r in (mock_redis_tier, mock_redis_quantai):
                mock_r.get.side_effect = lambda k: {
                    wallet_free_key: "10.0",
                    f"user:{free_id}:ai_chats:count": "1"
                }.get(k)
                mock_r.incrbyfloat.return_value = 9.997

            mock_llm.astream.reset_mock()
            res = await client.post(
                "/api/v1/quantai/chat",
                headers={"Authorization": f"Bearer {token_free}"},
                json={
                    "message": "Tell me about my workspace",
                    "context": "circuit-builder",
                    "client_context": {"placed_gates_count": 9, "wires": 4}
                }
            )
            assert res.status_code == 200
            args, kwargs = mock_llm.astream.call_args
            user_msg = args[0][-1]
            assert "User message: Tell me about my workspace" in user_msg.content
            assert "placed_gates_count" not in user_msg.content

            # PRO tier: workspace state context injected
            for mock_r in (mock_redis_tier, mock_redis_quantai):
                mock_r.get.side_effect = lambda k: {
                    wallet_pro_key: "10.0",
                    f"user:{pro_id}:ai_chats:count": "1"
                }.get(k)
                mock_r.incrbyfloat.return_value = 9.997

            mock_llm.astream.reset_mock()
            res = await client.post(
                "/api/v1/quantai/chat",
                headers={"Authorization": f"Bearer {token_pro}"},
                json={
                    "message": "Tell me about my workspace",
                    "context": "circuit-builder",
                    "client_context": {"placed_gates_count": 9, "wires": 4}
                }
            )
            assert res.status_code == 200
            args, kwargs = mock_llm.astream.call_args
            user_msg = args[0][-1]
            assert "User message: Tell me about my workspace" in user_msg.content
            assert "Active Subsystem Context: circuit-builder" in user_msg.content
            assert "placed_gates_count" in user_msg.content

    finally:
        await cleanup_test_user(free_id)
        await cleanup_test_user(pro_id)
