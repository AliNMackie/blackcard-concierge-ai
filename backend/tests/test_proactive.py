import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.main import app
from app.database import Base, get_db
from app.models import User, DailyBiometrics, DailyInsight

# Use a test-specific SQLite database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_concierge.db"

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
async def test_simulate_morning_briefing_flow(client, test_db):
    # 1. Setup Mock User
    user = User(id="test_user_proactive", role="client")
    test_db.add(user)
    await test_db.commit()

    # 2. Mock Auth (Simplified for test)
    # We'll need a way to bypass get_current_user or mock it.
    # For this test, we can override it.
    from app.auth import get_current_user
    async def override_get_current_user():
        return type('AuthUser', (), {'uid': 'test_user_proactive', 'email': 'test@example.com', 'is_trainer': False, 'is_client': True, 'is_admin': False})
    
    app.dependency_overrides[get_current_user] = override_get_current_user

    # 3. Trigger Simulation
    payload = {
        "sleep_score": 42,
        "recovery_status": "RED"
    }
    
    response = await client.post("/api/v1/concierge/simulate-morning", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "insight_headline" in data
    assert "actionable_advice" in data
    assert "suggested_plan_override" in data
    
    # Check DB persistence
    from sqlalchemy import select
    stmt = select(DailyInsight).where(DailyInsight.user_id == "test_user_proactive")
    result = await test_db.execute(stmt)
    insight = result.scalar_one_or_none()
    
    assert insight is not None
    assert insight.insight_headline == data["insight_headline"]
    
    # 4. Test GET /today
    get_response = await client.get("/api/v1/concierge/today")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["insight_headline"] == data["insight_headline"]
    assert get_data["actionable_advice"] == data["actionable_advice"]

    # Cleanup overrides
    app.dependency_overrides = {}

