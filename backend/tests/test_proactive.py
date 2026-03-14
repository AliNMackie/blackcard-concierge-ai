import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.main import app
from app.models import User, DailyBiometrics, DailyInsight

@pytest.mark.asyncio
async def test_simulate_morning_briefing_flow(api_client: AsyncClient, db_session):
    # 1. Setup Mock User
    user_id = "test_user_proactive"
    user = User(id=user_id, role="client")
    db_session.add(user)
    await db_session.commit()

    # 2. Mock Auth
    from app.auth import get_current_user
    async def override_get_current_user():
        class MockUser:
            def __init__(self):
                self.uid = user_id
                self.email = 'test@example.com'
                self.role = 'client'
                self.is_trainer = False
                self.is_client = True
                self.is_admin = False
                self.db_user = user
            
        return MockUser()
    
    app.dependency_overrides[get_current_user] = override_get_current_user

    # 3. Trigger Simulation
    payload = {
        "sleep_score": 42,
        "recovery_status": "RED"
    }
    
    response = await api_client.post("/api/v1/concierge/simulate-morning", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "insight_headline" in data
    assert "actionable_advice" in data
    assert "suggested_plan_override" in data
    
    # Check DB persistence
    stmt = select(DailyInsight).where(DailyInsight.user_id == user_id)
    result = await db_session.execute(stmt)
    insight = result.scalar_one_or_none()
    
    assert insight is not None
    assert insight.insight_headline == data["insight_headline"]
    
    # 4. Test GET /today
    get_response = await api_client.get("/api/v1/concierge/today")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["insight_headline"] == data["insight_headline"]
    assert get_data["actionable_advice"] == data["actionable_advice"]

    # Cleanup overrides
    app.dependency_overrides.clear()
