import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text, Column, String
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector
import uuid

Base = declarative_base()

class TestVector(Base):
    __tablename__ = "test_vectors"
    id = Column(String, primary_key=True)
    vec = Column(Vector(3))

async def test_pgvector():
    engine = create_async_engine("postgresql+asyncpg://postgres:mysecretpassword@localhost:5436/postgres", echo=True)
    
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        v = TestVector(id=str(uuid.uuid4()), vec=[0.1, 0.2, 0.3])
        session.add(v)
        await session.commit()
        print("Successfully inserted vector!")
        
        # Query it back using cosine distance
        res = await session.execute(text("SELECT id FROM test_vectors ORDER BY vec <=> '[0.1, 0.2, 0.3]' LIMIT 1"))
        print(f"Retrieved ID: {res.scalar()}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_pgvector())
