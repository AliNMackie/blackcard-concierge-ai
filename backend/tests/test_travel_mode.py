import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datetime import datetime

from app.main import app
from app.database import Base, get_db
from app.models import User, DailyBiometrics, DailyInsight

# Use a test-specific SQLite database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_travel.db"

@pytest.fixture(scope="function")
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_factory() as session:
        yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def client(test_db):
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_travel_mode_full_flow(client, test_db):
    # 1. Setup Mock User
    user = User(id="test_travel_user", role="client")
    test_db.add(user)
    await test_db.commit()

    # 2. Mock Auth
    from app.auth import get_current_user
    async def override_get_current_user():
        return type('AuthUser', (), {'uid': 'test_travel_user', 'email': 'travel@example.com', 'is_trainer': False, 'is_client': True, 'is_admin': False})
    
    app.dependency_overrides[get_current_user] = override_get_current_user

    # 3. Toggle Travel Mode ON
    payload = {
        "is_traveling": True,
        "equipment_constraint": "Hotel Gym (Dumbbells Only)"
    }
    
    response = await client.patch("/api/v1/users/travel-status", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_traveling"] is True
    assert data["equipment_constraint"] == "Hotel Gym (Dumbbells Only)"

    # 4. Verify in DB
    await test_db.refresh(user)
    assert user.is_traveling is True
    assert user.equipment_constraint == "Hotel Gym (Dumbbells Only)"

    # 5. Check if simulation reflects travel mode (logic check)
    # We can't easily check the *internal* prompt, but we can check if it runs
    sim_payload = {
        "sleep_score": 85,
        "recovery_status": "GREEN"
    }
    sim_response = await client.post("/api/v1/concierge/simulate-morning", json=sim_payload)
    assert sim_response.status_code == 200
    
    # 6. Toggle Travel Mode OFF
    off_payload = {
        "is_traveling": False,
        "equipment_constraint": "Full Gym"
    }
    response = await client.patch("/api/v1/users/travel-status", json=off_payload)
    assert response.status_code == 200
    assert response.json()["is_traveling"] is False

    # Cleanup overrides
    app.dependency_overrides = {}
