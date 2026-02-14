import logging
from typing import List, Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_google_vertexai import VertexAIEmbeddings

import app.database
from app.models import DocumentChunk
from app.config import settings, logger

class Retriever:
    def __init__(self):
        self.embeddings_model = None
        self._init_embeddings()

    def _init_embeddings(self):
        try:
            if settings.is_production():
                self.embeddings_model = VertexAIEmbeddings(model_name="text-embedding-004")
            else:
                try: 
                    # Try to init mock if available, or just set None
                    self.embeddings_model = None
                    logger.info("Retriever: Using MOCK embeddings (Dev Mode)")
                except:
                    pass
        except Exception as e:
            logger.error(f"Retriever: Failed to init Vertex AI: {e}")

    async def get_embedding(self, text: str) -> List[float]:
        if self.embeddings_model:
            return self.embeddings_model.embed_query(text)
        else:
            # Mock vector
            return [0.1] * 768

    async def retrieve_protocol(self, query: str, tags: List[str] = [], k: int = 3) -> str:
        """
        Retrieves relevant context strings.
        """
        try:
            # 1. Embed Query
            query_vector = await self.get_embedding(query)
            
            # 2. DB Search
            if not app.database.AsyncSessionLocal:
                return "Error: Database not initialized."

            async with app.database.AsyncSessionLocal() as session:
                stmt = select(DocumentChunk)
                
                # Hybrid Filter: Tags
                # Note: pgvector + complex filters can be tricky. 
                # For MVP, we filter strictly if tags provided, OR just boost?
                # Let's filter strictly if tags are present
                if tags:
                    # JSONB/Array containment? 
                    # Our model 'tags' is JSON, so we can use JSON operators if database supports it.
                    # Or simple ILIKE for MVP if tags are stored as text string? 
                    # Model has `tags = mapped_column(JSON)`. 
                    # Let's Skip complex tag filtering for step 1, focus on semantic.
                    pass
                
                # Semantic Search
                # Check pgvector syntax: order_by(DocumentChunk.embedding.cosine_distance(query_vector))
                stmt = stmt.order_by(DocumentChunk.embedding.cosine_distance(query_vector)).limit(k)
                
                result = await session.execute(stmt)
                chunks = result.scalars().all()
                
                if not chunks:
                    return ""
                
                # Format
                context_parts = []
                for c in chunks:
                    context_parts.append(f"Source: {c.source}\nContent: {c.content}")
                
                return "\n\n".join(context_parts)
                
        except Exception as e:
            logger.error(f"Retrieval Error: {e}")
            return ""

# Global Instance
retriever = Retriever()
