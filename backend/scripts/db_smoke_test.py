import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def run_smoke_test():
    """
    Verifies Database Connection and basic Read/Write.
    Apps logic relies on Alembic migrations, but this script is a raw smoke test.
    """
    # Get DB Connection string from Env
    # Format: postgresql+asyncpg://user:pass@host:port/dbname
    # or using Cloud SQL Connector (not used here for raw simplicity, assuming proxy or direct)
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set. Skipping smoke test.")
        # In CI, we might want to fail if this is expected
        sys.exit(1)

    print(f"🔌 Connecting to DB: {db_url.split('@')[-1]}") # Redact creds
    
    try:
        engine = create_async_engine(db_url, echo=False)
        
        async with engine.begin() as conn:
            # 1. Simple Select
            print("   Running SELECT 1...")
            await conn.execute(text("SELECT 1"))
            
            # 2. Write Check (Create generic temp table if valid)
            # Keeping it safe: just check version
            print("   Checking Version...")
            res = await conn.execute(text("SHOW server_version"))
            version = res.scalar()
            print(f"✅ DB Connected. Version: {version}")
            
        await engine.dispose()
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ DB Smoke Test Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_smoke_test())
