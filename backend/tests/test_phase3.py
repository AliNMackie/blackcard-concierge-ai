import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models import User
from app.main import app

@pytest.mark.asyncio
async def test_onboarding_saves_to_db(api_client: AsyncClient, db_session):
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
    
    # Mock Auth
    from app.auth import get_current_user
    async def override_get_current_user():
        return type('AuthUser', (), {
            'uid': 'testuser123', 'email': 'test1@example.com', 'role': 'client',
            'is_trainer': False, 'is_client': True, 'is_admin': False, 'db_user': None
        })
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await api_client.post("/api/v1/users/profile", json=payload, headers=headers)
    
    # Clean up
    app.dependency_overrides.clear()
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["profile_data"]["primary_goal"] == "Hypertrophy"
    
    # Verify in DB
    stmt = select(User).where(User.id == "testuser123")
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    assert user is not None
    assert user.profile_data["age"] == 28


@pytest.mark.asyncio
async def test_paywall_blocks_4th_request(api_client: AsyncClient, db_session):
    headers = {"Authorization": "Bearer MOCK_TOKEN_testuser456"}
    
    # Mock Auth
    from app.auth import get_current_user
    async def override_get_current_user():
        return type('AuthUser', (), {
            'uid': 'testuser456', 'email': 'test456@example.com', 'role': 'client',
            'is_trainer': False, 'is_client': True, 'is_admin': False, 'db_user': None
        })
    app.dependency_overrides[get_current_user] = override_get_current_user

    # Needs a mock workout plan
    payload = {
        "current_workout_plan": {"name": "Test", "exercises": []},
        "user_feedback": "Too heavy"
    }
    
    # Ensure user has 0 uses
    user = User(id="testuser456", role="client", tier="free", ai_usage_count=0)
    db_session.add(user)
    await db_session.commit()
        
    # First 3 requests should succeed
    # We mock the service call to avoid Gemini
    from unittest.mock import patch
    with patch("app.api.routes.coach.generate_coach_adaptation", return_value={"coaching_cue": "test", "adapted_plan": {}}):
        for i in range(3):
            response = await api_client.post("/api/v1/coach/adapt", json=payload, headers=headers)
            assert response.status_code == 200
            
        # 4th request should be blocked (ai_usage_count=3)
        response_4 = await api_client.post("/api/v1/coach/adapt", json=payload, headers=headers)
        assert response_4.status_code == 403
        
        error_data = response_4.json()
        assert error_data["detail"]["code"] == "paywall_required"
        assert error_data["detail"]["limit"] == 3
    
    app.dependency_overrides.clear()
