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

@pytest.fixture(scope="function")
async def api_client(override_get_db):
    """Provides an AsyncClient for testing the FastAPI app."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    # Use a fresh client for every test to avoid loop pollution
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def db_session(db_engine):
    """Provides a fresh async session from the database module's engine."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        # Use close() instead of rollback() to avoid some teardown race conditions in asyncpg
        await session.close()

@pytest.fixture(scope="session")
def db_engine():
    """Provides the async engine from the database module."""
    import app.database as db
    from sqlalchemy.pool import NullPool
    from sqlalchemy.ext.asyncio import create_async_engine
    
    # We create a new engine with NullPool for tests to avoid sharing connections across loops
    # which causes "another operation in progress" in asyncpg.
    engine = create_async_engine(
        db.async_engine.url if (db.async_engine and hasattr(db.async_engine, 'url')) else "postgresql+asyncpg://postgres:mysecretpassword@localhost:5436/postgres",
        poolclass=NullPool
    )
    return engine

@pytest.fixture
async def override_get_db(postgres_container):
    """Overrides the get_db dependency in the FastAPI app."""
    from app.main import app
    from app.database import AsyncSessionLocal, get_db
    
    async def _get_db_override():
        async with AsyncSessionLocal() as session:
            yield session
            
    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.clear()

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
