import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models import User
from app.main import app

@pytest.mark.asyncio
async def test_travel_mode_full_flow(api_client: AsyncClient, db_session):
    # 1. Setup Mock User
    user = User(id="test_travel_user", role="client")
    db_session.add(user)
    await db_session.commit()

    # 2. Mock Auth
    from app.auth import get_current_user
    async def override_get_current_user():
        return type('AuthUser', (), {'uid': 'test_travel_user', 'email': 'travel@example.com', 'is_trainer': False, 'is_client': True, 'is_admin': False, 'role': 'client', 'db_user': user})
    
    app.dependency_overrides[get_current_user] = override_get_current_user

    # 3. Toggle Travel Mode ON
    payload = {
        "is_traveling": True,
        "equipment_constraint": "Hotel Gym (Dumbbells Only)"
    }
    
    response = await api_client.patch("/api/v1/users/travel-status", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_traveling"] is True
    assert data["equipment_constraint"] == "Hotel Gym (Dumbbells Only)"

    # 4. Verify in DB
    await db_session.refresh(user)
    assert user.is_traveling is True
    assert user.equipment_constraint == "Hotel Gym (Dumbbells Only)"

    # 5. Check if simulation reflects travel mode (logic check)
    # Mocking the concierge response to avoid hitting real Gemini
    from unittest.mock import patch
    with patch("app.api.routes.concierge.generate_morning_briefing", return_value={"insight_headline": "Travel Check", "actionable_advice": "Travel workout ready"}):
        sim_payload = {
            "sleep_score": 85,
            "recovery_status": "GREEN"
        }
        sim_response = await api_client.post("/api/v1/concierge/simulate-morning", json=sim_payload)
        assert sim_response.status_code == 200
        data = sim_response.json()
        assert data["insight_headline"] == "Travel Check"
    
    # 6. Toggle Travel Mode OFF
    off_payload = {
        "is_traveling": False,
        "equipment_constraint": "Full Gym"
    }
    response = await api_client.patch("/api/v1/users/travel-status", json=off_payload)
    assert response.status_code == 200
    assert response.json()["is_traveling"] is False

    # Cleanup overrides
    app.dependency_overrides.clear()
