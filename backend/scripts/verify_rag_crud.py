import asyncio
import os
import sys
from sqlalchemy import text, select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models import DocumentChunk
from app.database import Base
from app.config import logger

# Force DB Connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:mysecretpassword@localhost:5436/postgres")

async def verify_rag_crud():
    logger.info(f"Connecting to {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    try:
        # 1. Reset Tables (Clean Slate)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database reset complete.")

        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # 2. Check Extension
            logger.info("Checking pgvector extension...")
            result = await session.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
            assert result.scalar() == 1
            print("✅ pgvector extension enabled.")

            # 3. Create Chunk
            logger.info("Testing Insert...")
            embedding = [0.1] * 768
            chunk = DocumentChunk(
                content="Test content",
                source="Test Source",
                embedding=embedding,
                tags=["test"]
            )
            session.add(chunk)
            await session.commit()
            print("✅ Inserted chunk.")

            # 4. Read Chunk
            logger.info("Testing Read...")
            stmt = select(DocumentChunk).where(DocumentChunk.source == "Test Source")
            result = await session.execute(stmt)
            retrieved = result.scalar_one()
            assert retrieved.content == "Test content"
            assert retrieved.embedding is not None
            print("✅ Read chunk successful.")

            # 5. Vector Search
            logger.info("Testing Vector Search...")
            # Insert 2 more
            vec1 = [1.0] + [0.0] * 767
            vec2 = [0.0] + [1.0] * 767
            c1 = DocumentChunk(content="A", embedding=vec1, source="A")
            c2 = DocumentChunk(content="B", embedding=vec2, source="B")
            session.add_all([c1, c2])
            await session.commit()

            stmt = select(DocumentChunk).order_by(DocumentChunk.embedding.l2_distance(vec1)).limit(1)
            result = await session.execute(stmt)
            best_match = result.scalar_one()
            assert best_match.content == "A"
            print("✅ Vector search successful (found A).")

    except Exception as e:
        logger.error(f"❌ Verification Failed: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_rag_crud())
