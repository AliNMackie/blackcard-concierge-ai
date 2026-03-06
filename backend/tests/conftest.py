import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.database import Base

@pytest.fixture(scope="session")
def postgres_container():
    """
    Connect to the docker-compose test database (backend-db-test-1).
    Does NOT spin up a new container. Requires `docker-compose -f docker-compose.test.yml up -d`
    """
    return "postgresql+asyncpg://postgres:mysecretpassword@localhost:5436/postgres"

@pytest.fixture(scope="session", autouse=True)
async def setup_db(postgres_container):
    """Force database initialization with the test container URL."""
    from app.config import settings
    import app.database as db
    
    # 1. Update settings
    settings.DATABASE_URL = postgres_container
    
    # 2. Force re-initialization of the connection pool
    await db.init_connection_pool()
    
    # 3. Create tables
    async with db.async_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Cleanup
    if db.async_engine:
        await db.async_engine.dispose()
