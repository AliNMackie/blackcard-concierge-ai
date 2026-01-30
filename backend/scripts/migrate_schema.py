"""
Schema Migration Script
Adds missing columns to production tables that were added after initial deployment.
Run this script against Cloud SQL to fix schema mismatches.
"""
import asyncio
import sys
import os

# Add the parent directory (backend) to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import database
from app.database import init_connection_pool
from sqlalchemy import text

async def migrate():
    print("Initializing DB Connection...")
    await init_connection_pool()
    
    if not database.async_engine:
        print("Failed to initialize database connection. Check config.")
        return

    async with database.async_engine.begin() as conn:
        print("Running schema migrations...")
        
        # Add coach_style column to users table if it doesn't exist
        try:
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS coach_style VARCHAR DEFAULT 'hyrox_competitor';
            """))
            print("✓ Added coach_style column to users table")
        except Exception as e:
            print(f"  coach_style: {e}")
        
        # Add is_traveling column to users table if it doesn't exist
        try:
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS is_traveling BOOLEAN DEFAULT FALSE;
            """))
            print("✓ Added is_traveling column to users table")
        except Exception as e:
            print(f"  is_traveling: {e}")
            
        print("Schema migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
