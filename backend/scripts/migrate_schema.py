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
        
        # === NEW: Authentication fields ===
        
        # Add email column for user authentication
        try:
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS email VARCHAR UNIQUE;
            """))
            print("✓ Added email column to users table")
        except Exception as e:
            print(f"  email: {e}")
        
        # Add role column for role-based access control
        try:
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'client';
            """))
            print("✓ Added role column to users table")
        except Exception as e:
            print(f"  role: {e}")
        
        # Add trainer_id column for trainer-client linking
        try:
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS trainer_id VARCHAR REFERENCES users(id);
            """))
            print("✓ Added trainer_id column to users table")
        except Exception as e:
            print(f"  trainer_id: {e}")
        
        # Create indexes for efficient lookups
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_trainer ON users(trainer_id);
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
            """))
            print("✓ Created indexes for email, trainer_id, role")
        except Exception as e:
            print(f"  indexes: {e}")
        
        # Update existing demo user to admin role
        try:
            await conn.execute(text("""
                UPDATE users SET role = 'admin' WHERE id = '1' OR id = 'demo_user';
            """))
            print("✓ Updated demo user to admin role")
        except Exception as e:
            print(f"  demo user update: {e}")
            
        print("Schema migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())

