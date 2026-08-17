import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from datetime import datetime, timezone
from models import APIKey
from core.database import async_session_factory
import uuid

@pytest.mark.asyncio
async def test_api_key_lifecycle(pro_user):
    """Test API key creation, listing, deletion, and rotation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a new API key
        create_res = await client.post("/developer/keys", json={
            "label": "Test Key",
            "tier": "api_pro"
        }, headers={"Authorization": f"Bearer temp"}) # Assuming testing middleware or auth bypass is configured
        
        # We need an access token for the pro_user to authenticate requests.
        from security import create_access_token
        access_token = create_access_token({"sub": str(pro_user.id)})
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        create_res = await client.post("/developer/keys", json={
            "label": "Test Key",
            "tier": "api_pro"
        }, headers=headers)
        
        assert create_res.status_code == 200
        data = create_res.json()
        # The plaintext secret is returned as "api_key" and only ever once.
        assert "api_key" in data
        assert data["label"] == "Test Key"
        key_id = data["id"]
        
        # List API keys
        list_res = await client.get("/developer/keys", headers=headers)
        assert list_res.status_code == 200
        keys = list_res.json()
        assert len(keys) == 1
        assert keys[0]["id"] == key_id
        
        # Rotate API key
        rotate_res = await client.post(f"/developer/keys/{key_id}/rotate", headers=headers)
        assert rotate_res.status_code == 200
        rotate_data = rotate_res.json()
        assert "api_key" in rotate_data
        assert rotate_data["id"] == key_id
        assert rotate_data["api_key"] != data["api_key"]  # Should be a new raw key
        
        # Delete API key
        delete_res = await client.delete(f"/developer/keys/{key_id}", headers=headers)
        assert delete_res.status_code == 200
        
        # List again to ensure it's deleted
        list_res2 = await client.get("/developer/keys", headers=headers)
        assert list_res2.status_code == 200
        keys2 = list_res2.json()
        assert len(keys2) == 0
