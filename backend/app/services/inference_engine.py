"""
Situational Similarity Engine — Level 5 Ambient Intelligence

Retrieves historical InferenceStates that mathematically align with
the user's current situation using pgvector cosine distance:
Distance = 1 - (V_current . V_past) / (||V_current|| ||V_past||)
"""
import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.contextual_memory import InferenceState
from app.graph import gemini_client

logger = logging.getLogger("elite-concierge")


class SimilarityQuery(BaseModel):
    user_id: str
    current_context: str = Field(
        description="Text description of the user state to embed (e.g., 'Slept 5hrs, back pain')"
    )
    limit: int = 3


class SimilarStateResult(BaseModel):
    id: str
    context_summary: str
    resulting_outcome: str | None
    similarity_score: float  # 1.0 (identical) down to 0.0 (orthogonal)


async def embed_text(text: str) -> List[float]:
    """
    Mock function to represent calling the Vertex AI text-embedding model.
    In production, this would use textembedding-gecko or text-embedding-preview.
    Here we return a deterministic 768-dim mock vector.
    """
    # Simply hash the text into a 768d vector for mock deterministic behavior
    import hashlib
    h = hashlib.sha256(text.encode('utf-8')).digest()
    
    # Expand 32 bytes to 768 floats
    vector = []
    for i in range(768):
        val = (h[i % 32] / 128.0) - 1.0  # Range -1 to 1
        vector.append(val)
        
    return vector


async def find_similar_situations(query: SimilarityQuery, db: AsyncSession) -> List[SimilarStateResult]:
    """
    Given a new real-time state, query the InferenceState table to find
    the top N most similar past states using pgvector cosine distance (`<=>`).
    """
    logger.info(f"[InferenceEngine] Embedding context: '{query.current_context[:50]}...'")
    current_vector = await embed_text(query.current_context)
    
    # 1 - (V1 <=> V2) converts pgvector's cosine distance into cosine similarity (0 to 1)
    similarity_expr = 1 - InferenceState.state_vector.cosine_distance(current_vector)
    
    stmt = (
        select(InferenceState, similarity_expr.label("similarity_score"))
        .where(InferenceState.user_id == query.user_id)
        .order_by(InferenceState.state_vector.cosine_distance(current_vector))
        .limit(query.limit)
    )
    
    try:
        result = await db.execute(stmt)
        rows = result.all()
        
        results = []
        for state, score in rows:
            results.append(
                SimilarStateResult(
                    id=state.id,
                    context_summary=state.context_summary,
                    resulting_outcome=state.resulting_outcome,
                    similarity_score=float(score),
                )
            )
            logger.info(f"[InferenceEngine] Match: {state.id} (Score: {score:.3f})")
            
        return results
        
    except Exception as e:
        logger.error(f"[InferenceEngine] pgvector query failed: {e}")
        # In a real scenario, we might want to fail gracefully. 
        # For this prototype we'll return an empty list or raise.
        raise
