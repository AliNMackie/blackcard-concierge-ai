import asyncio
import os
import glob
import app.database 
from app.models import DocumentChunk
from app.config import settings, logger
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_vertexai import VertexAIEmbeddings

# Configuration
KB_DIR = os.path.join(os.path.dirname(__file__), "../docs/knowledge_base")
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

async def ingest_knowledge_base():
    """
    Main ingestion loop.
    1. Load MD files.
    2. Split text.
    3. Embed.
    4. Store.
    """
    logger.info("Starting Knowledge Base Ingestion...")
    
    # Check DB Connection String
    db_url = os.getenv("DATABASE_URL")
    logger.info(f"Target Database: {db_url}")
    
    await app.database.init_connection_pool()
    logger.info("Creating tables if they don't exist...")
    await app.database.create_tables()
    
    # 1. Initialize Vertex AI Embeddings
    try:
        if settings.is_production():
             embeddings_model = VertexAIEmbeddings(model_name="text-embedding-004")
        else:
            logger.warning("Running in MOCK mode for embeddings.")
            embeddings_model = None
    except Exception as e:
        logger.error(f"Failed to init Vertex AI: {e}")
        return

    # 2. Process Files
    # Normalize path for Windows
    kb_dir_abs = os.path.abspath(KB_DIR)
    files = glob.glob(os.path.join(kb_dir_abs, "*.md"))
    logger.info(f"Found {len(files)} documents in {kb_dir_abs}")

    total_chunks = 0
    
    if not app.database.AsyncSessionLocal:
        logger.error("Database connection failed - AsyncSessionLocal is None.")
        return

    async with app.database.AsyncSessionLocal() as session:
        for file_path in files:
            filename = os.path.basename(file_path)
            logger.info(f"Processing {filename}...")
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Extract Metadata 
            tags = []
            if "**Tags**:" in content:
                for line in content.split("\n"):
                    if line.startswith("**Tags**:"):
                        raw_tags = line.split(":", 1)[1].strip()
                        tags = [t.strip() for t in raw_tags.split(",")]
                        break
            
            # Split
            splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
            chunks = splitter.split_text(content)
            
            # Embed & Store
            batch_models = []
            for i, text_chunk in enumerate(chunks):
                # Embed
                vector = []
                if embeddings_model:
                    try:
                        vector = embeddings_model.embed_query(text_chunk)
                    except Exception as e:
                        logger.error(f"Embedding failed for chunk {i}: {e}")
                        continue
                else:
                    # Mock Vector (768 dims) - Deterministic mock for testing
                    # Generate a slightly different vector based on chunk index to avoid identical vectors
                    # but keep it normalized-ish
                    base_val = (i + 1) * 0.001
                    vector = [base_val] * 768

                doc = DocumentChunk(
                    content=text_chunk,
                    source=filename,
                    embedding=vector,
                    tags=tags,
                    metadata_json={"chunk_index": i, "total_chunks": len(chunks)}
                )
                batch_models.append(doc)
            
            # Clear old chunks for this source (Idempotency) - Optional
            # await session.execute(delete(DocumentChunk).where(DocumentChunk.source == filename))
            
            session.add_all(batch_models)
            total_chunks += len(batch_models)
            
        await session.commit()
    
    logger.info(f"Ingestion Complete. Added {total_chunks} chunks.")

if __name__ == "__main__":
    # Fix for Windows loop
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(ingest_knowledge_base())
