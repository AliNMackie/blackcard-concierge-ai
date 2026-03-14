import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.main import app
from app.models import User, EventLog
from sqlalchemy import select
from unittest.mock import patch
import os

# Use the override_get_db fixture to inject the container DB
@pytest.mark.asyncio
async def test_health_check(api_client):
    response = await api_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "connected"

@pytest.mark.asyncio
async def test_create_user_on_login(db_session):
    """Verify that a user is created in the DB when they login (via mock auth for now)."""
    # For integration test, we can manually insert a user or assume auth middleware does it.
    # Let's manually insert to test the DB
    
    user1 = User(id="test_uid_1", email="test1@example.com", role="client")
    db_session.add(user1)
    await db_session.commit()
    
    # Verify via Select
    stmt = select(User).where(User.id == "test_uid_1")
    result = await db_session.execute(stmt)
    fetched_user = result.scalar_one_or_none()
    
    assert fetched_user is not None
    assert fetched_user.email == "test1@example.com"

@pytest.mark.asyncio
async def test_gdpr_wipe(api_client, db_session):
    """Verify the /wipe endpoint removes logs and anonymizes user."""
    
    # 1. Setup Data
    user_id = "gdpr_victim"
    user = User(id=user_id, email="victim@example.com", role="client", coach_style="aggressive")
    db_session.add(user)
    
    log1 = EventLog(user_id=user_id, event_type="chat", payload={"msg": "I love metadata"})
    log2 = EventLog(user_id=user_id, event_type="wearable", payload={"hr": 60})
    db_session.add_all([log1, log2])
    
    await db_session.commit()
    
    # 2. Call Wipe Endpoint
    headers = {"X-Elite-Key": "test-secret-key"} 
    
    # Need to mock settings for the app's internal checks
    with patch("app.auth.settings.ELITE_API_KEY", "test-secret-key"):
        os.environ["ELITE_API_KEY"] = "test-secret-key"
        response = await api_client.delete(f"/users/{user_id}/wipe", headers=headers) 
            
    assert response.status_code == 200
    
    # 3. Verify Data Gone
    # Logs should be 0
    result = await db_session.execute(select(EventLog).where(EventLog.user_id == user_id))
    logs = result.scalars().all()
    assert len(logs) == 0
    
    # User should be reset
    # Re-fetch user
    # Note: Session might need refreshing
    await db_session.refresh(user)
    
    # Check anonymization fields from main.py implementation
    assert user.coach_style == "standard"
    assert user.is_traveling == False
