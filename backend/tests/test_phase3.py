import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.main import app
from app.models import User
from app.database import AsyncSessionLocal

@pytest.mark.asyncio
async def test_onboarding_saves_to_db():
    # Mock Headers to bypass Firebase and use Mock user
    headers = {"Authorization": "Bearer MOCK_TOKEN_testuser123"}
    
    payload = {
        "height": "180cm",
        "weight": "85kg",
        "age": 28,
        "gender": "Male",
        "primary_goal": "Hypertrophy",
        "injuries": "None",
        "days_per_week": 4
    }
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/users/profile", json=payload, headers=headers)
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["profile_data"]["primary_goal"] == "Hypertrophy"
    
    # Verify in DB
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.id == "testuser123")
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        assert user is not None
        assert user.profile_data["age"] == 28


@pytest.mark.asyncio
async def test_paywall_blocks_4th_request():
    headers = {"Authorization": "Bearer MOCK_TOKEN_testuser456"}
    
    # Needs a mock workout plan
    payload = {
        "current_workout_plan": {"name": "Test", "exercises": []},
        "user_feedback": "Too heavy"
    }
    
    # Ensure user has 0 uses
    async with AsyncSessionLocal() as session:
        user = User(id="testuser456", role="client", tier="free", ai_usage_count=0)
        session.add(user)
        await session.commit()
        
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # First 3 requests should succeed
        for i in range(3):
            response = await ac.post("/api/v1/coach/adapt", json=payload, headers=headers)
            assert response.status_code == 200
            
        # 4th request should be blocked
        response_4 = await ac.post("/api/v1/coach/adapt", json=payload, headers=headers)
        assert response_4.status_code == 403
        
        error_data = response_4.json()
        assert error_data["detail"]["code"] == "paywall_required"
        assert error_data["detail"]["limit"] == 3
