import os
import sys
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models as DBmodels
from core.database import async_session_factory
from main import app

def get_unique_suffix():
    return os.urandom(4).hex()

@pytest.mark.asyncio
async def test_public_badge_generation():
    suffix = get_unique_suffix()
    email = f"badge_user_{suffix}@example.com"
    
    # 1. Setup User and MonitoredTarget in DB
    async with async_session_factory() as session:
        user = DBmodels.User(email=email, name="Badge User", hashed_password="pwd", is_active=True)
        session.add(user)
        await session.flush()
        user_id = user.id
        
        target = DBmodels.MonitoredTarget(
            user_id=user_id,
            target_type="domain",
            target_value="testbadge.com",
            schedule_interval="daily",
            last_scan_score=92.0 # Grade A+
        )
        session.add(target)
        await session.commit()
        target_id = target.id

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 2. Get valid badge
            res = await client.get(f"/api/v1/public/badge/{target_id}")
            assert res.status_code == 200
            assert "image/svg+xml" in res.headers["content-type"]
            svg_content = res.text
            assert "<svg" in svg_content
            assert "#10b981" in svg_content # Emerald green background for A+
            assert "A (92%)" in svg_content
            
            # 3. Get invalid badge fallback
            res_invalid = await client.get("/api/v1/public/badge/999999")
            assert res_invalid.status_code == 200
            assert "image/svg+xml" in res_invalid.headers["content-type"]
            svg_invalid = res_invalid.text
            assert "<svg" in svg_invalid
            assert "#64748b" in svg_invalid # Slate grey background
            assert "N/A" in svg_invalid

    finally:
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM monitored_targets WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            await session.commit()


@pytest.mark.asyncio
async def test_circuit_sharing_and_permissions():
    suffix_a = get_unique_suffix()
    suffix_b = get_unique_suffix()
    email_a = f"user_a_{suffix_a}@example.com"
    email_b = f"user_b_{suffix_b}@example.com"
    
    # 1. Setup two users and one circuit in DB
    async with async_session_factory() as session:
        user_a = DBmodels.User(email=email_a, name="User A", hashed_password="pwd", is_active=True)
        user_b = DBmodels.User(email=email_b, name="User B", hashed_password="pwd", is_active=True)
        session.add_all([user_a, user_b])
        await session.flush()
        
        user_a_id = user_a.id
        user_b_id = user_b.id
        
        circuit = DBmodels.Circuit(
            user_id=user_a_id,
            name="Superposition Test",
            circuit_data='[{"name": "h", "qubits": [0], "params": []}]',
            is_interactive=True
        )
        session.add(circuit)
        await session.commit()
        
        circuit_id = circuit.id

    try:
        from core.auth import create_access_token
        token_a = create_access_token(user_a)
        token_b = create_access_token(user_b)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 2. Try to share User A's circuit using User B's token (should be 403)
            res_unauth = await client.post(
                f"/api/v1/circuits/{circuit_id}/share",
                headers={"Authorization": f"Bearer {token_b}"}
            )
            assert res_unauth.status_code == 403
            
            # 3. Share User A's circuit as User A (should succeed)
            res_share = await client.post(
                f"/api/v1/circuits/{circuit_id}/share",
                headers={"Authorization": f"Bearer {token_a}"}
            )
            assert res_share.status_code == 200
            data_share = res_share.json()
            assert data_share["status"] == "success"
            assert data_share["is_public"] is True
            share_slug = data_share["share_slug"]
            assert share_slug is not None
            
            # 4. Fetch the circuit publicly (unauthenticated)
            res_pub = await client.get(f"/api/v1/public/circuits/{share_slug}")
            assert res_pub.status_code == 200
            data_pub = res_pub.json()
            assert data_pub["name"] == "Superposition Test"
            assert data_pub["author_name"] == "User A"
            assert data_pub["circuit_data"] == '[{"name": "h", "qubits": [0], "params": []}]'
            
            # 5. Unshare User A's circuit as User A
            res_unshare = await client.post(
                f"/api/v1/circuits/{circuit_id}/unshare",
                headers={"Authorization": f"Bearer {token_a}"}
            )
            assert res_unshare.status_code == 200
            assert res_unshare.json()["is_public"] is False
            
            # 6. Fetch the circuit publicly again (should be 404 now)
            res_pub_revoked = await client.get(f"/api/v1/public/circuits/{share_slug}")
            assert res_pub_revoked.status_code == 404

    finally:
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM circuits WHERE user_id IN (:uid_a, :uid_b)"), {"uid_a": user_a_id, "uid_b": user_b_id})
            await session.execute(text("DELETE FROM users WHERE id IN (:uid_a, :uid_b)"), {"uid_a": user_a_id, "uid_b": user_b_id})
            await session.commit()
