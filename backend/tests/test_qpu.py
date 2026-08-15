import os
import sys
import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models as DBmodels
import models_billing
from core.database import async_session_factory
from main import app

def get_unique_suffix():
    return os.urandom(4).hex()

@pytest.mark.asyncio
async def test_qpu_credit_deductions():
    suffix = get_unique_suffix()
    email = f"qpu_user_{suffix}@example.com"

    # Register test user
    async with async_session_factory() as session:
        user = DBmodels.User(email=email, name="QPU User", hashed_password="pwd", is_active=True)
        session.add(user)
        await session.flush()
        
        # Give enough credits for one run: 2000.0 credits (requires 1000 + 10 * 10 = 1100 credits for 10 shots)
        wallet = models_billing.WalletBalance(user_id=user.id, balance_credits=2000.0)
        session.add(wallet)
        await session.commit()
        user_id = user.id

    try:
        from core.auth import create_access_token
        access_token = create_access_token(user)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            payload = {
                "qasm_string": 'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[2] q;\nbit[2] c;\nh q[0];\ncx q[0], q[1];\nc = measure q;',
                "shots": 10,
                "backend_choice": "IBM Quantum",
                "noise_model": "Ideal"
            }

            # 1. Execute on IBM Quantum (should succeed and deduct 1100 credits)
            res = await client.post(
                "/api/v1/simulator/execute",
                json=payload,
                headers=headers
            )
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "success"
            assert data["qpu_telemetry"] is not None
            assert data["qpu_telemetry"]["provider"] == "IBM Quantum"
            assert "surcharge" in data["warnings"][0]

            # Verify deduction in DB: 2000 - 1100 = 900 credits
            async with async_session_factory() as session:
                stmt = select(models_billing.WalletBalance).where(models_billing.WalletBalance.user_id == user_id)
                db_res = await session.execute(stmt)
                db_wallet = db_res.scalar_one()
                assert float(db_wallet.balance_credits) == 900.0

            # 2. Second execution (should fail due to insufficient balance: requires 1100 but has 900)
            res2 = await client.post(
                "/api/v1/simulator/execute",
                json=payload,
                headers=headers
            )
            assert res2.status_code == 402
            assert "Insufficient wallet balance" in res2.json()["detail"]

    finally:
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM usage_events WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM wallet_balances WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            await session.commit()
