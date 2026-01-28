import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from google.cloud.sql.connector import Connector, IPTypes
from app.config import settings, logger

# Database Models Base
class Base(DeclarativeBase):
    pass

# Global DB components
async_engine = None
AsyncSessionLocal = None

async def init_connection_pool():
    global async_engine
    
    # 1. Local Dev / Explicit URL (Postgres or SQLite)
    if settings.DATABASE_URL:
        logger.info(f"Connecting to DB via URL: {settings.DATABASE_URL}")
        async_engine = create_async_engine(settings.DATABASE_URL)
        return

    # 2. Cloud SQL Connector (Production/Staging)
    if settings.DB_INSTANCE_CONNECTION_NAME:
        logger.info(f"Connecting to Cloud SQL: {settings.DB_INSTANCE_CONNECTION_NAME}")
        
        from google.cloud.sql.connector import Connector, IPTypes
        import os
        
        # We'll use a local connector inside the creator to avoid event loop issues
        # although usually a global one is fine if initialized in the right loop.
        # However, making it lazy inside getconn is safest.
        
        connector = None

        async def getconn():
            nonlocal connector
            current_loop = asyncio.get_running_loop()
            
            # Ensure connector uses the current running loop
            if connector is None or connector._loop != current_loop:
                logger.info("Initializing Cloud SQL Connector (New Loop detected)")
                connector = Connector(loop=current_loop)
            
            db_pass = os.getenv("DB_PASS", "placeholder")
            conn = await connector.connect_async(
                settings.DB_INSTANCE_CONNECTION_NAME,
                "asyncpg",
                user=settings.DB_USER,
                password=db_pass,
                db=settings.DB_NAME,
                ip_type=IPTypes.PRIVATE,
            )
            return conn

        async_engine = create_async_engine(
            "postgresql+asyncpg://",
            async_creator=getconn,
        )
        return
    
    logger.warning("No Database Configured. Persistence will be disabled.")


async def get_db():
    if not async_engine:
        await init_connection_pool()
        
    if not async_engine:
        # Fallback if config is missing (e.g. tests without mock)
        yield None
        return

    async_session = async_sessionmaker(async_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session

async def create_tables():
    """Simple auto-migration for MVP"""
    if async_engine:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
