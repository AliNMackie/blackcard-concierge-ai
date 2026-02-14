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

@pytest.fixture(scope="session")
def db_engine(postgres_container):
    """Create a single DB engine for the session (Synchronous wrapper)."""
    engine = create_async_engine(postgres_container, echo=False)
    
    # Sync wrapper for async setup
    async def setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
            
    asyncio.run(setup())
        
    yield engine
    
    # Sync wrapper for async teardown
    asyncio.run(engine.dispose())
