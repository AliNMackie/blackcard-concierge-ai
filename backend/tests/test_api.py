import pytest
from httpx import AsyncClient
from sqlalchemy import text

@pytest.mark.asyncio
async def test_health_check(api_client: AsyncClient):
    response = await api_client.get("/health")
    
    if response.status_code != 200:
        print(f"Health check failed with {response.status_code}: {response.text}")
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "connected"

@pytest.mark.asyncio
async def test_direct_db_smoke(db_session):
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1
