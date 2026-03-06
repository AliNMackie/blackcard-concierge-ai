import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    
    if response.status_code != 200:
        print(f"Health check failed with {response.status_code}: {response.text}")
        
    assert response.status_code == 200
@pytest.mark.asyncio
async def test_direct_db_smoke():
    from app.database import AsyncSessionLocal
    from sqlalchemy import text
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1
