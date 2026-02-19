"""
Test suite for email verification.

Run with: pytest tests/test_email_verification.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import json
import os

# Set test environment
os.environ["ENV"] = "test"
os.environ["AUTH_SECRET_KEY"] = "test_secret_key_12345678901234567890123456789012"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:5173"
os.environ["VERIFICATION_REQUIRED"] = "true"
os.environ["VERIFICATION_GRACE_PERIOD_HOURS"] = "168"  # 7 days

from main import app
from database import Base, SessionLocal, engine
import DBmodels

# Create test database
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[DBmodels.get_db_session] = override_get_db


class TestEmailVerification:
    """Test email verification flow."""

    def test_registration_creates_unverified_user(self):
        """New user should have email_verified=False."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "StrongPass123!",
                "name": "New User"
            }
        )
        assert response.status_code == 200

        # Check user in DB
        from database import SessionLocal
        db = SessionLocal()
        try:
            user = db.query(DBmodels.User).filter(DBmodels.User.email == "newuser@example.com").first()
            assert user is not None
            assert user.email_verified is False
        finally:
            db.close()

    def test_login_without_verification_within_grace_period(self):
        """User should be able to login within grace period without verifying."""
        # Register
        client.post(
            "/api/auth/register",
            json={
                "email": "grace@example.com",
                "password": "StrongPass123!",
                "name": "Grace User"
            }
        )

        # Login immediately should succeed (within 7-day grace)
        response = client.post(
            "/api/auth/login",
            json={
                "email": "grace@example.com",
                "password": "StrongPass123!"
            }
        )
        assert response.status_code == 200

    def test_login_requires_verification_after_grace_period(self):
        """User should be blocked if grace period passed and email not verified."""
        # Register
        client.post(
            "/api/auth/register",
            json={
                "email": "olduser@example.com",
                "password": "StrongPass123!",
                "name": "Old User"
            }
        )

        # Simulate user created 8 days ago by modifying DB directly
        from database import SessionLocal
        from datetime import datetime, timedelta
        db = SessionLocal()
        try:
            user = db.query(DBmodels.User).filter(DBmodels.User.email == "olduser@example.com").first()
            user.created_at = datetime.utcnow() - timedelta(days=8)
            db.commit()
        finally:
            db.close()

        # Login attempt should be blocked
        response = client.post(
            "/api/auth/login",
            json={
                "email": "olduser@example.com",
                "password": "StrongPass123!"
            }
        )
        assert response.status_code == 403
        assert "verification" in response.json()["detail"].lower()

    def test_verification_flow(self):
        """Test full verification: token creation, verification, login."""
        # Register
        client.post(
            "/api/auth/register",
            json={
                "email": "verifyflow@example.com",
                "password": "StrongPass123!",
                "name": "Verify Flow"
            }
        )

        # Create verification token manually (in production, requested via /verify/send)
        from database import SessionLocal
        from datetime import datetime, timedelta
        import uuid
        db = SessionLocal()
        try:
            user = db.query(DBmodels.User).filter(DBmodels.User.email == "verifyflow@example.com").first()
            token = str(uuid.uuid4())
            expires = datetime.utcnow() + timedelta(hours=24)
            vt = DBmodels.EmailVerificationToken(
                user_id=user.id,
                token=token,
                expires_at=expires
            )
            db.add(vt)
            user.verification_sent_at = datetime.utcnow()
            db.commit()
            user_id = user.id
        finally:
            db.close()

        # Verify with token
        response = client.post("/api/auth/verify/confirm", json={"token": token})
        assert response.status_code == 200
        assert response.json()["message"] == "Email verified successfully"

        # Check user is verified
        db = SessionLocal()
        try:
            user = db.query(DBmodels.User).filter(DBmodels.User.id == user_id).first()
            assert user.email_verified is True
        finally:
            db.close()

        # Login should now succeed
        response = client.post(
            "/api/auth/login",
            json={
                "email": "verifyflow@example.com",
                "password": "StrongPass123!"
            }
        )
        assert response.status_code == 200

    def test_resend_verification(self):
        """Test resending verification email."""
        # Register
        client.post(
            "/api/auth/register",
            json={
                "email": "resend@example.com",
                "password": "StrongPass123!",
                "name": "Resend Test"
            }
        )

        # Request resend
        response = client.post(
            "/api/auth/verify/resend",
            json={"email": "resend@example.com"}
        )
        assert response.status_code == 200
        assert "Verification email sent" in response.json()["message"]

        # Check token was created
        from database import SessionLocal
        db = SessionLocal()
        try:
            user = db.query(DBmodels.User).filter(DBmodels.User.email == "resend@example.com").first()
            tokens = db.query(DBmodels.EmailVerificationToken).filter(
                DBmodels.EmailVerificationToken.user_id == user.id
            ).all()
            assert len(tokens) >= 1
        finally:
            db.close()

    def test_verification_status_endpoint(self):
        """Check /verify/status returns correct status."""
        # Register
        client.post(
            "/api/auth/register",
            json={
                "email": "status@example.com",
                "password": "StrongPass123!",
                "name": "Status Test"
            }
        )

        # Get auth header by logging in
        login_resp = client.post(
            "/api/auth/login",
            json={
                "email": "status@example.com",
                "password": "StrongPass123!"
            }
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Check status
        response = client.get("/api/auth/verify/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "email_verified" in data
        assert data["email_verified"] is False

    def test_invalid_verification_token(self):
        """Invalid token should fail."""
        response = client.post(
            "/api/auth/verify/confirm",
            json={"token": "invalid-token-1234"}
        )
        assert response.status_code == 400
        assert "Invalid verification token" in response.json()["detail"]

    def test_expired_verification_token(self):
        """Expired token should fail."""
        # Create expired token directly in DB
        from database import SessionLocal
        from datetime import datetime, timedelta
        import uuid
        db = SessionLocal()
        try:
            # Create a user
            from auth_utils import hash_password
            user = DBmodels.User(
                email="expired@example.com",
                password=hash_password("StrongPass123!"),
                name="Expired User",
                email_verified=False
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            token = str(uuid.uuid4())
            expires = datetime.utcnow() - timedelta(hours=1)  # Expired
            vt = DBmodels.EmailVerificationToken(
                user_id=user.id,
                token=token,
                expires_at=expires
            )
            db.add(vt)
            db.commit()
        finally:
            db.close()

        response = client.post(
            "/api/auth/verify/confirm",
            json={"token": token}
        )
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])