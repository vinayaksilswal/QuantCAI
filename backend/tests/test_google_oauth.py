import pytest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import models as DBmodels
from core.database import SessionLocal
from routers.auth import router as auth_router

app = FastAPI()
app.include_router(auth_router)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_get_auth_config():
    client = TestClient(app)
    response = client.get("/api/auth/config")
    assert response.status_code == 200
    data = response.json()
    assert "google_client_id" in data
    assert "google_redirect_uri" in data

@patch("routers.auth.verify_google_id_token")
def test_oauth_google_new_user(mock_verify, db_session):
    # Mock Google returns valid token payload
    mock_verify.return_value = {
        "email": "new_google_user@example.com",
        "name": "Google User"
    }

    client = TestClient(app)
    response = client.post("/api/auth/oauth/google", json={"id_token": "fake_token"})
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in response.cookies

    # Verify user was created in DB
    user = db_session.query(DBmodels.User).filter(DBmodels.User.email == "new_google_user@example.com").first()
    assert user is not None
    assert user.name == "Google User"
    assert user.email_verified is True

@patch("routers.auth.verify_google_id_token")
def test_oauth_google_existing_user(mock_verify, db_session):
    # Create existing user
    user = DBmodels.User(
        email="existing_google_user@example.com",
        hashed_password="hashed_dummy_password",
        name="Existing User",
        is_active=True,
        is_blocked=False,
        email_verified=False
    )
    db_session.add(user)
    db_session.commit()

    mock_verify.return_value = {
        "email": "existing_google_user@example.com",
        "name": "Updated Google Name"
    }

    client = TestClient(app)
    response = client.post("/api/auth/oauth/google", json={"id_token": "fake_token"})
    
    assert response.status_code == 200
    
    # Reload from DB and verify user
    db_session.refresh(user)
    assert user.name == "Existing User"
