import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import select, text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models as DBmodels
from core.database import async_session_factory
from worker import execute_scheduled_scans

def get_unique_suffix():
    return os.urandom(4).hex()

@pytest.mark.asyncio
@patch("worker.scan_tls_pqc")
async def test_scheduled_scan_drift_alert(mock_scan):
    suffix = get_unique_suffix()
    email = f"scheduler_user_{suffix}@example.com"

    # Mock domain scan result returning a lower score (80.0) than initial (95.0)
    mock_scan.return_value = {
        "domain": "testdrift.com",
        "cbom_summary": {
            "pqc_readiness_pct": 80.0
        }
    }

    # Register user and monitored target
    async with async_session_factory() as session:
        user = DBmodels.User(email=email, name="Scheduler User", hashed_password="pwd", is_active=True)
        session.add(user)
        await session.flush()
        
        target = DBmodels.MonitoredTarget(
            user_id=user.id,
            target_type="domain",
            target_value="testdrift.com",
            schedule_interval="daily",
            last_scan_score=95.0
        )
        session.add(target)
        await session.commit()
        user_id = user.id
        target_id = target.id

    try:
        # Run Celery task directly (synchronously)
        result = execute_scheduled_scans()
        assert result["status"] == "success"
        assert result["scans_executed"] == 1
        assert result["alerts_created"] == 1

        # Check database for generated SecurityAlert and updated target score
        async with async_session_factory() as session:
            # Check monitored target score updated
            stmt_t = select(DBmodels.MonitoredTarget).where(DBmodels.MonitoredTarget.id == target_id)
            res_t = await session.execute(stmt_t)
            db_target = res_t.scalar_one()
            assert db_target.last_scan_score == 80.0

            # Check Alert created
            stmt_a = select(DBmodels.SecurityAlert).where(DBmodels.SecurityAlert.target_id == target_id)
            res_a = await session.execute(stmt_a)
            db_alert = res_a.scalar_one()
            assert "Cryptographic Drift Detected" in db_alert.title
            assert "95.0% to 80.0%" in db_alert.message

    finally:
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM security_alerts WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM monitored_targets WHERE user_id = :uid"), {"uid": user_id})
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            await session.commit()
