import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models import User

@pytest.mark.asyncio
async def test_onboarding_flow(api_client: AsyncClient, db_session):
    # 1. Mock Auth
    from app.auth import get_current_user
    from app.main import app
    
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
    
    response = await api_client.post("/api/v1/users/onboard", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "onboarded"
    assert data["profile_data"]["onboarded"] is True
    assert data["profile_data"]["goal"] == "hypertrophy"

    # 3. Verify DB persistence
    stmt = select(User).where(User.id == "test_onboard_user")
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    assert user is not None
    assert user.profile_data["age"] == 35
    assert user.profile_data["goal"] == "hypertrophy"
    assert user.profile_data["onboarded"] is True

    # 4. Test paywall: Simulate 3 adaptations then expect block
    user.ai_usage_count = 3
    user.tier = "free"
    await db_session.commit()

    # This should return 403 because the user hit the free limit
    adapt_payload = {
        "current_workout_plan": {"exercises": []},
        "user_feedback": "Too heavy"
    }
    # Fixed typo: changed /api/v1/api/v1/coach/adapt to /api/v1/coach/adapt
    adapt_response = await api_client.post("/api/v1/coach/adapt", json=adapt_payload)

    assert adapt_response.status_code == 403
    assert adapt_response.json()["detail"]["code"] == "paywall_required"

    # Cleanup
    app.dependency_overrides.clear()
