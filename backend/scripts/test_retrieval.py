import asyncio
import os
import app.database
from rag.retriever import retriever
from app.config import settings, logger

async def test_retrieval():
    # Force DB URL if not set (for local testing convenience)
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@localhost:5435/postgres"

    logger.info(f"Initializing Database... {os.getenv('DATABASE_URL')}")
    await app.database.init_connection_pool()
    
    # Pre-check: Ensure tables exist (just in case)
    # await app.database.create_tables()

    query = "How do I optimize sleep and recovery?"
    logger.info(f"Querying: {query}")
    
    try:
        context = await retriever.retrieve_protocol(query, tags=["recovery"])
        
        print("\n--- Retrieved Context ---\n")
        print(context)
        print("\n-------------------------\n")
        
        if "Physiological Sighs" in context or "Magnesium" in context:
            print("SUCCESS: Relevant protocol found.")
        else:
            print("FAILURE: Context did not contain Expected keywords.")
            print(f"Got: {context[:100]}...")
            
    except Exception as e:
        logger.error(f"Test Failed: {e}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_retrieval())
