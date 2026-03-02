import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.auth import get_current_user

async def check_persona():
    # Mock Auth
    async def override_get_current_user():
        return type('AuthUser', (), {'uid': 'manual_check_user', 'email': 'test@example.com', 'is_trainer': False, 'is_client': True, 'is_admin': False})
    
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "sleep_score": 35,
            "recovery_status": "RED"
        }
        print(f"\n[TESTING] Simulating RED recovery for Blackcard persona...")
        response = await ac.post("/api/v1/concierge/simulate-morning", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n--- CONCIERGE BRIEFING ---")
            print(f"HEADLINE: {data['insight_headline']}")
            print(f"ADVICE: {data['actionable_advice']}")
            print(f"OVERRIDE: {data['suggested_plan_override']}")
            print(f"---------------------------\n")
        else:
            print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(check_persona())
