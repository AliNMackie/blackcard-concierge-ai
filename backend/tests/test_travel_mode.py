import pytest
import httpx
import json
from app.models import User
from sqlalchemy import select

@pytest.mark.asyncio
async def test_travel_mode_flow(test_client, db_session):
    # 1. Setup User 1 if not exists
    stmt = select(User).where(User.id == "1")
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        user = User(id="1", role="client")
        db_session.add(user)
        await db_session.commit()

    # 2. Toggle Travel Mode ON
    headers = {"X-Elite-Key": "dev-bypass"} # Using dev bypass for simplicity in tests
    payload = {
        "is_traveling": True,
        "equipment_constraint": "Hotel Gym (Dumbbells Only)"
    }
    
    response = await test_client.patch("/api/v1/users/travel-status", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_traveling"] is True
    assert data["equipment_constraint"] == "Hotel Gym (Dumbbells Only)"

    # 3. Verify in DB
    await db_session.refresh(user)
    assert user.is_traveling is True
    assert user.equipment_constraint == "Hotel Gym (Dumbbells Only)"

    # 4. Mock Simulation (Just check if it runs without error now that RAG has travel logic)
    # We simulate a briefing which should now check user travel status
    sim_response = await test_client.post("/api/v1/concierge/simulate-morning", headers=headers)
    assert sim_response.status_code == 200
    sim_data = sim_response.json()
    assert "insight_headline" in sim_data

    # 5. Toggle Travel Mode OFF
    off_payload = {
        "is_traveling": False,
        "equipment_constraint": "Full Gym"
    }
    response = await test_client.patch("/api/v1/users/travel-status", json=off_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["is_traveling"] is False
