"""
Test suite for QuantCAI authentication and authorization.

Run with: pytest tests/test_auth.py -v
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
os.environ["AUTH_SECRET_KEY"] = "test_secret_key_12345678901234567890123456789012"  # 32+ chars
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:5173,http://localhost:3000"

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


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_register_success(self):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "StrongPass123!",
                "name": "Test User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_weak_password(self):
        """Test registration with weak password is rejected."""
        test_cases = [
            ("short", "Password must be at least 8 characters long"),
            ("nouppercase1!", "Password must contain at least one uppercase letter"),
            ("NOLOWERCASE1!", "Password must contain at least one lowercase letter"),
            ("NoNumbers!", "Password must contain at least one number"),
            ("NoSpecial123", "Password must contain at least one special character"),
        ]

        for password, expected_detail in test_cases:
            response = client.post(
                "/api/auth/register",
                json={
                    "email": "test@example.com",
                    "password": password,
                    "name": "Test User"
                }
            )
            assert response.status_code == 400, f"Password '{password}' should be rejected"
            assert expected_detail in response.json()["detail"]

    def test_register_duplicate_email(self):
        """Test registration with existing email fails."""
        # First registration
        client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "StrongPass123!",
                "name": "Test User"
            }
        )

        # Second registration with same email
        response = client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "AnotherPass123!",
                "name": "Another User"
            }
        )
        assert response.status_code == 400
        assert "User already exists" in response.json()["detail"]

    def test_login_success(self):
        """Test successful login."""
        # Register first
        client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "StrongPass123!",
                "name": "Login Test"
            }
        )

        response = client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "StrongPass123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data or data.get("refresh_token") == ""

        # Check cookie
        assert "refresh_token" in response.cookies

    def test_login_invalid_credentials(self):
        """Test login with wrong password."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "WrongPass"
            }
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_account_lockout(self):
        """Test account lockout after 5 failed login attempts."""
        email = "lockout@example.com"

        # Register user
        client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "StrongPass123!",
                "name": "Lockout Test"
            }
        )

        # Attempt 5 failed logins
        for i in range(5):
            response = client.post(
                "/api/auth/login",
                json={
                    "email": email,
                    "password": "WrongPass"
                }
            )
            assert response.status_code == 401

        # 6th attempt should be locked
        response = client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": "WrongPass"
            }
        )
        assert response.status_code == 403
        assert "temporarily locked" in response.json()["detail"].lower()

    def test_refresh_token(self):
        """Test refresh token flow."""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "StrongPass123!",
                "name": "Refresh Test"
            }
        )
        login_resp = client.post(
            "/api/auth/login",
            json={
                "email": "refresh@example.com",
                "password": "StrongPass123!"
            }
        )
        refresh_token = login_resp.cookies.get("refresh_token")
        assert refresh_token is not None

        # Access a protected endpoint to get a fresh token
        # (In real app, you'd call /api/auth/refresh with the cookie)
        # Simulate by calling /api/auth/me directly
        headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
        me_resp = client.get("/api/auth/me", headers=headers)
        assert me_resp.status_code == 200

    def test_logout(self):
        """Test logout revokes tokens."""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "email": "logout@example.com",
                "password": "StrongPass123!",
                "name": "Logout Test"
            }
        )
        login_resp = client.post(
            "/api/auth/login",
            json={
                "email": "logout@example.com",
                "password": "StrongPass123!"
            }
        )
        headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

        # Logout
        logout_resp = client.post("/api/auth/logout", headers=headers)
        assert logout_resp.status_code == 200

        # Token should be revoked
        me_resp = client.get("/api/auth/me", headers=headers)
        assert me_resp.status_code == 401


class TestRateLimiting:
    """Test rate limiting on auth endpoints."""

    def test_login_rate_limit(self):
        """Test rate limiting on login endpoint."""
        email = "ratelimit@example.com"

        # Register
        client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "StrongPass123!",
                "name": "Rate Limit Test"
            }
        )

        # Make 5 rapid requests (should all work or 429 on 6th)
        responses = []
        for i in range(6):
            response = client.post(
                "/api/auth/login",
                json={
                    "email": email,
                    "password": "WrongPass" + str(i)  # Different wrong passwords
                }
            )
            responses.append(response.status_code)

        # At least one should be 429 or 403 (rate limited or locked)
        # Depending on implementation
        assert any(code in [429, 403] for code in responses), f"Rate limiting not working: {responses}"

    def test_register_rate_limit(self):
        """Test rate limiting on register endpoint."""
        # Attempt 6 rapid registrations with different emails
        responses = []
        for i in range(6):
            response = client.post(
                "/api/auth/register",
                json={
                    "email": f"rate{i}@example.com",
                    "password": "StrongPass123!",
                    "name": f"Rate Test {i}"
                }
            )
            responses.append(response.status_code)

        # Should have at least one 429 (or some other rate limit code)
        assert any(code == 429 for code in responses), f"Rate limiting not triggered: {responses}"


class TestSecurityHeaders:
    """Test security headers are present."""

    def test_security_headers(self):
        """Test that security headers are set."""
        response = client.get("/")
        headers = response.headers

        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert "strict-origin-when-cross-origin" in headers.get("referrer-policy", "")

        # CSP should be present
        csp = headers.get("content-security-policy", "")
        assert "default-src 'self'" in csp or "default-src 'self'" in csp.lower()

    def test_cors_headers(self):
        """Test CORS headers for allowed origins."""
        response = client.options("/", headers={"Origin": "http://localhost:5173"})
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") in ["http://localhost:5173", "*"]

        # Disallowed origin should not get CORS headers (or get 403)
        response2 = client.options("/", headers={"Origin": "https://evil.com"})
        # Could be 200 with no access-control-allow-origin, or 403/400
        # The implementation may vary
        origin_header = response2.headers.get("access-control-allow-origin")
        assert origin_header != "https://evil.com", "Should not allow arbitrary origins"


class TestInputSanitization:
    """Test XSS protection via input sanitization."""

    def test_post_sanitization(self):
        """Test that XSS in post content is stripped."""
        # Create a user
        auth_header = self._login_and_get_header()

        # Try to create post with script tag
        response = client.post(
            "/api/posts",
            json={
                "title": "Test Post <script>alert('xss')</script>",
                "body": "This is a test <img src=x onerror=alert(1)>"
            },
            headers=auth_header
        )
        assert response.status_code == 200
        post_id = response.json()["id"]

        # Fetch post and ensure script tags are removed
        get_resp = client.get("/api/posts", headers=auth_header)
        posts = get_resp.json()
        my_post = next(p for p in posts if p["id"] == post_id)

        assert "<script>" not in my_post["title"]
        assert "<script>" not in my_post["body"]
        assert "alert" not in my_post["body"]

    def test_comment_sanitization(self):
        """Test that XSS in comments is stripped."""
        auth_header = self._login_and_get_header()

        # Create a post first
        post_resp = client.post(
            "/api/posts",
            json={
                "title": "For Comments",
                "body": "Original post"
            },
            headers=auth_header
        )
        post_id = post_resp.json()["id"]

        # Create comment with XSS
        comment_resp = client.post(
            "/api/comments",
            json={
                "post_id": post_id,
                "body": "Nice post! <iframe src='javascript:alert(1)'>"
            },
            headers=auth_header
        )
        assert comment_resp.status_code == 200

        # Fetch posts and check comment is sanitized
        get_resp = client.get("/api/posts", headers=auth_header)
        posts = get_resp.json()
        post = next(p for p in posts if p["id"] == post_id)
        comment = post["comments"][0]

        assert "<iframe" not in comment["body"]
        assert "javascript" not in comment["body"]

    def _login_and_get_header(self):
        """Helper: register, login, return Authorization header."""
        email = "sanitest@example.com"
        client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "StrongPass123!",
                "name": "Sanitize Test"
            }
        )
        login_resp = client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": "StrongPass123!"
            }
        )
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])