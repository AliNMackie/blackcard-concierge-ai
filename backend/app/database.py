from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.config import settings, logger

# Create Base for models
Base = declarative_base()

# Global engine and session factory
async_engine = None
AsyncSessionLocal = None

async def init_connection_pool():
    global async_engine, AsyncSessionLocal
    
    database_url = settings.DATABASE_URL
    if not database_url:
        logger.warning("DATABASE_URL not set. Database features will fail.")
        return

    # Create Async Engine
    async_engine = create_async_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        future=True,
    )

    # Create Session Factory
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    logger.info("Database connection pool initialized.")

async def get_db():
    """Dependency for ensuring a database session."""
    if AsyncSessionLocal is None:
         # Fallback or raise error? For now, yield nothing or raise
         raise RuntimeError("Database not initialized.")
         
    async with AsyncSessionLocal() as session:
        yield session

async def create_tables():
    """Simple auto-migration for MVP. Added manual column check for Travel Mode."""
    if async_engine:
        async with async_engine.begin() as conn:
            # 1. Standard SQLAlchemy create
            await conn.run_sync(Base.metadata.create_all)
            
            # 2. Manual migration: Add 'is_traveling' if missing
            try:
                # Direct SQL check and add for Users table
                await conn.execute(
                    text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_traveling BOOLEAN DEFAULT FALSE;")
                )
                logger.info("Database Migration Check: is_traveling column verified/added.")
            except Exception as e:
                # If column exists or other error, log it but don't crash
                logger.warning(f"Note: Table migration check skipped/failed: {e}")
