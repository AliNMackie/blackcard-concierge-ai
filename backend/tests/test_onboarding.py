import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.main import app
from app.database import Base, get_db
from app.models import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_onboarding.db"

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
async def test_onboarding_flow(client, test_db):
    # 1. Mock Auth
    from app.auth import get_current_user
    async def override_get_current_user():
        return type('AuthUser', (), {
            'uid': 'test_onboard_user',
            'email': 'onboard@example.com',
            'is_trainer': False,
            'is_client': True,
            'is_admin': False,
            'role': 'client',
            'db_user': None
        })
    app.dependency_overrides[get_current_user] = override_get_current_user

    # 2. Submit onboarding
    payload = {
        "age": 35,
        "gender": "Male",
        "current_weight": "85",
        "target_weight": "80",
        "goal": "hypertrophy",
        "injuries": "Lower back pain",
        "days_per_week": 4
    }
    
    response = await client.post("/api/v1/users/onboard", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "onboarded"
    assert data["profile_data"]["onboarded"] is True
    assert data["profile_data"]["goal"] == "hypertrophy"

    # 3. Verify DB persistence
    stmt = select(User).where(User.id == "test_onboard_user")
    result = await test_db.execute(stmt)
    user = result.scalar_one_or_none()
    
    assert user is not None
    assert user.profile_data["age"] == 35
    assert user.profile_data["goal"] == "hypertrophy"
    assert user.profile_data["onboarded"] is True

    # 4. Test paywall: Simulate 3 adaptations then expect block
    user.ai_usage_count = 3
    user.tier = "free"
    await test_db.commit()

    # This should return 403 because the user hit the free limit
    adapt_payload = {
        "current_workout_plan": {"exercises": []},
        "user_feedback": "Too heavy"
    }
    adapt_response = await client.post("/api/v1/api/v1/coach/adapt", json=adapt_payload)

    assert adapt_response.status_code == 403
    assert adapt_response.json()["detail"]["code"] == "paywall_required"

    # Cleanup
    app.dependency_overrides = {}
