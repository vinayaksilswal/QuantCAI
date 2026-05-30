import os
import sys
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi import Request, HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models as DBmodels
from core.database import async_session_factory, engine
from main import app  # imports main app with tutor route registered
from security import create_access_token
from tutor import IntentClassifier, SimulationResponse

def get_unique_suffix():
    return os.urandom(4).hex()

# Mock return data models for structured outputs
class MockIntent:
    def __init__(self, intent):
        self.intent = intent

class MockSimulation:
    def __init__(self, qasm, explanation):
        self.openqasm_code = qasm
        self.explanation = explanation


@pytest.mark.asyncio
@patch("tutor.redis_client", new_callable=AsyncMock)
@patch("tutor.llm", new_callable=AsyncMock)
@patch("tutor.structured_classifier", new_callable=AsyncMock)
@patch("tutor.structured_simulation", new_callable=AsyncMock)
async def test_tutor_workflow_and_tier_limits(
    mock_structured_simulation,
    mock_structured_classifier,
    mock_llm,
    mock_redis
):
    # Setup test users
    suffix = get_unique_suffix()
    email_free = f"free_student_{suffix}@example.com"
    email_pro = f"pro_student_{suffix}@example.com"
    
    async with async_session_factory() as session:
        # Create users
        user_free = DBmodels.User(
            email=email_free,
            hashed_password="mock_password_hash",
            name="Free Learner",
            role=DBmodels.UserRole.LEARNER,
            is_active=True
        )
        user_pro = DBmodels.User(
            email=email_pro,
            hashed_password="mock_password_hash",
            name="Pro Learner",
            role=DBmodels.UserRole.LEARNER,
            is_active=True
        )
        session.add_all([user_free, user_pro])
        await session.flush()
        
        # Add subscription plans
        sub_free = DBmodels.Subscription(
            user_id=user_free.id,
            plan=DBmodels.SubscriptionPlan.FREE,
            status=DBmodels.SubscriptionStatus.ACTIVE
        )
        sub_pro = DBmodels.Subscription(
            user_id=user_pro.id,
            plan=DBmodels.SubscriptionPlan.PRO,
            status=DBmodels.SubscriptionStatus.ACTIVE
        )
        session.add_all([sub_free, sub_pro])
        await session.commit()
        
        user_free_id = user_free.id
        user_pro_id = user_pro.id

    try:
        # Setup tokens
        payload_free = {
            "sub": str(user_free_id),
            "type": "access",
            "role": "learner",
            "token_version": 0
        }
        token_free = create_access_token(payload_free)
        
        payload_pro = {
            "sub": str(user_pro_id),
            "type": "access",
            "role": "learner",
            "token_version": 0
        }
        token_pro = create_access_token(payload_pro)
        
        # Configure mocks
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        
        # Test Case 1: Conceptual Question (Free User)
        mock_structured_classifier.ainvoke.return_value = MockIntent("conceptual_question")
        mock_llm.ainvoke.return_value = MagicMock(content="Socratic response checking understanding.")
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 1. Ask a question
            headers = {"Authorization": f"Bearer {token_free}"}
            res = await client.post(
                "/tutor/chat",
                headers=headers,
                json={"message": "What is superposition?", "conversation_id": "conv-123"}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["conversation_id"] == "conv-123"
            assert data["intent"] == "conceptual_question"
            assert "Socratic response" in data["response"]
            assert data["circuit_result"] is None
            
            # Verify usage event was created
            async with async_session_factory() as session:
                stmt = select(DBmodels.UsageEvent).where(DBmodels.UsageEvent.user_id == user_free_id)
                db_res = await session.execute(stmt)
                events = db_res.scalars().all()
                assert len(events) == 1
                assert events[0].event_type == DBmodels.UsageEventType.TUTOR_QUERY

        # Test Case 2: Math Help
        mock_structured_classifier.ainvoke.return_value = MockIntent("math_help")
        mock_llm.ainvoke.return_value = MagicMock(content="Step 1: calculate state $|\psi\\rangle$ using $\cos(\\theta/2)|0\\rangle$.")
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token_free}"}
            res = await client.post(
                "/tutor/chat",
                headers=headers,
                json={"message": "Calculate Bloch vector.", "conversation_id": "conv-123"}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["intent"] == "math_help"
            assert "$|\psi\\rangle$" in data["response"]
            
            async with async_session_factory() as session:
                stmt = select(DBmodels.UsageEvent).where(DBmodels.UsageEvent.user_id == user_free_id)
                db_res = await session.execute(stmt)
                events = db_res.scalars().all()
                assert len(events) == 2

        # Test Case 3: Off Topic
        mock_structured_classifier.ainvoke.return_value = MockIntent("off_topic")
        mock_llm.ainvoke.return_value = MagicMock(content="Let's redirect back to quantum computing.")
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token_free}"}
            res = await client.post(
                "/tutor/chat",
                headers=headers,
                json={"message": "What is the capital of France?", "conversation_id": "conv-123"}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["intent"] == "off_topic"
            assert "redirect" in data["response"]

        # Test Case 4: Free User Throttling (query limits)
        # Let's seed 3 more tutor queries to reach the limit of 5 (already have 3)
        async with async_session_factory() as session:
            for i in range(3):
                ev = DBmodels.UsageEvent(
                    user_id=user_free_id,
                    event_type=DBmodels.UsageEventType.TUTOR_QUERY,
                    credits_used=1,
                    metadata_={}
                )
                session.add(ev)
            await session.commit()
            
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Query #6 should fail
            headers = {"Authorization": f"Bearer {token_free}"}
            res = await client.post(
                "/tutor/chat",
                headers=headers,
                json={"message": "Can you explain entanglement?", "conversation_id": "conv-123"}
            )
            assert res.status_code == 200
            data = res.json()
            assert "reached your daily limit" in data["response"]
            
        # Test Case 5: Pro User is NOT Throttled
        # Seed 10 tutor queries for pro user
        async with async_session_factory() as session:
            for i in range(10):
                ev = DBmodels.UsageEvent(
                    user_id=user_pro_id,
                    event_type=DBmodels.UsageEventType.TUTOR_QUERY,
                    credits_used=1,
                    metadata_={}
                )
                session.add(ev)
            await session.commit()
            
        # Call chat for Pro user - should succeed
        mock_structured_classifier.ainvoke.return_value = MockIntent("conceptual_question")
        mock_llm.ainvoke.return_value = MagicMock(content="Pro response.")
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token_pro}"}
            res = await client.post(
                "/tutor/chat",
                headers=headers,
                json={"message": "Explain qubits.", "conversation_id": "conv-pro"}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["response"] == "Pro response."
            assert data["intent"] == "conceptual_question"

    finally:
        # Cleanup
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM usage_events WHERE user_id IN (:u1, :u2)"), {"u1": user_free_id, "u2": user_pro_id})
            await session.execute(text("DELETE FROM subscriptions WHERE user_id IN (:u1, :u2)"), {"u1": user_free_id, "u2": user_pro_id})
            await session.execute(text("DELETE FROM users WHERE id IN (:u1, :u2)"), {"u1": user_free_id, "u2": user_pro_id})
            await session.commit()


@pytest.mark.asyncio
@patch("tutor.redis_client", new_callable=AsyncMock)
@patch("tutor.structured_classifier", new_callable=AsyncMock)
@patch("tutor.structured_simulation", new_callable=AsyncMock)
@patch("tutor.get_simulation_status", new_callable=AsyncMock)
@patch("tutor.submit_simulation", new_callable=AsyncMock)
async def test_tutor_simulation_request(
    mock_submit_sim,
    mock_status_sim,
    mock_structured_simulation,
    mock_structured_classifier,
    mock_redis
):
    suffix = get_unique_suffix()
    email = f"tutor_sim_{suffix}@example.com"
    
    async with async_session_factory() as session:
        user = DBmodels.User(
            email=email,
            hashed_password="mock_password_hash",
            name="Sim Student",
            role=DBmodels.UserRole.LEARNER,
            is_active=True
        )
        session.add(user)
        await session.flush()
        
        sub = DBmodels.Subscription(
            user_id=user.id,
            plan=DBmodels.SubscriptionPlan.PRO,
            status=DBmodels.SubscriptionStatus.ACTIVE
        )
        session.add(sub)
        await session.commit()
        
        user_id = user.id

    try:
        payload = {
            "sub": str(user_id),
            "type": "access",
            "role": "learner",
            "token_version": 0
        }
        token = create_access_token(payload)
        
        # Mocks configuration
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        
        mock_structured_classifier.ainvoke.return_value = MockIntent("simulation_request")
        
        # Simulation output from LLM
        qasm_str = "OPENQASM 2.0;\ninclude \"qelib1.h\";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;"
        mock_structured_simulation.ainvoke.return_value = MockSimulation(
            qasm=qasm_str,
            explanation="Explanation of Bell State."
        )
        
        # Simulation engine submit mock
        mock_submit_res = MagicMock()
        mock_submit_res.job_id = "job-uuid-123"
        mock_submit_res.status = "queued"
        mock_submit_sim.return_value = mock_submit_res
        
        # Simulation engine status mock (completed result)
        mock_status_res = MagicMock()
        mock_status_res.status = "complete"
        mock_status_res.result = MagicMock()
        mock_status_res.result.model_dump.return_value = {
            "counts": {"00": 512, "11": 512},
            "execution_time_ms": 12.5,
            "shots": 1024,
            "circuit_depth": 3,
            "num_qubits": 2
        }
        mock_status_sim.return_value = mock_status_res
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token}"}
            res = await client.post(
                "/tutor/chat",
                headers=headers,
                json={"message": "Please simulate a Bell State.", "conversation_id": "conv-sim"}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["intent"] == "simulation_request"
            assert "OPENQASM 2.0" in data["response"]
            assert data["circuit_result"] is not None
            assert data["circuit_result"]["counts"] == {"00": 512, "11": 512}
            
            # Verify submit_simulation was called
            mock_submit_sim.assert_called_once()
            mock_status_sim.assert_called()

    finally:
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM usage_events WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM subscriptions WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            await session.commit()
