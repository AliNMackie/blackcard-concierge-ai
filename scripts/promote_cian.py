import asyncio
from sqlalchemy import select, update
from app.database import init_connection_pool, get_db
from app.models import User
import os

async def promote_user(email: str):
    await init_connection_pool()
    async for db in get_db():
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"Error: User with email {email} not found in database.")
            return
            
        print(f"Found user: {user.email} (UID: {user.id}). Current role: {user.role}")
        
        user.role = "trainer"
        await db.commit()
        print(f"Success! User {email} has been promoted to TRAINER.")
        return

if __name__ == "__main__":
    email = "Cd1fit23@gmail.com"
    asyncio.run(promote_user(email))
