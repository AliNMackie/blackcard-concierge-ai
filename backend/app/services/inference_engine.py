"""
Situational Similarity Engine — Level 5 Ambient Intelligence

Retrieves historical InferenceStates that mathematically align with
the user's current situation using pgvector cosine distance:
Distance = 1 - (V_current . V_past) / (||V_current|| ||V_past||)
"""
from typing import List, Optional
from pydantic import BaseModel, Field
import numpy as np

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import logger
from app.database import AsyncSessionLocal # or pass it in

from app.contextual_memory import InferenceState, BiomechanicalSignature


class SimilarityQuery(BaseModel):
    user_id: str
    current_context: str = Field(
        description="Text description of the user state to embed (e.g., 'Slept 5hrs, back pain')"
    )
    limit: int = 3


class SimilarityQueryBiomechanics(BaseModel):
    user_id: str
    movement_type: str
    embedding: List[float] = Field(description="Normalized 768d vector")
    limit: int = 5


class SimilarStateResult(BaseModel):
    id: str
    context_summary: str
    resulting_outcome: str | None
    similarity_score: float  # 1.0 (identical) down to 0.0 (orthogonal)


class SimilarBiomechanicsResult(BaseModel):
    id: str
    movement_type: str
    kinematic_notes: str | None
    similarity_score: float
    is_golden: bool


async def embed_text(text: str) -> List[float]:
    # ... (existing text embedding mock)
    import hashlib
    h = hashlib.sha256(text.encode('utf-8')).digest()
    vector = []
    for i in range(768):
        val = (h[i % 32] / 128.0) - 1.0
        vector.append(val)
    return vector


async def find_similar_situations(query: SimilarityQuery, db: AsyncSession) -> List[SimilarStateResult]:
    # ... (existing situational search)
    logger.info(f"[InferenceEngine] Embedding context: '{query.current_context[:50]}...'")
    current_vector = await embed_text(query.current_context)
    
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
        return [
            SimilarStateResult(
                id=s.id,
                context_summary=s.context_summary,
                resulting_outcome=s.resulting_outcome,
                similarity_score=float(score)
            ) for s, score in rows
        ]
    except Exception as e:
        logger.error(f"[InferenceEngine] pgvector query failed: {e}")
        raise


async def find_similar_biomechanics(query: SimilarityQueryBiomechanics, db: AsyncSession) -> List[SimilarBiomechanicsResult]:
    """
    Performs a cosine similarity search (<=>) against historical biomechanical signatures.
    Filters by user_id and movement_type.
    """
    logger.info(f"[InferenceEngine] Searching biomechanics for {query.movement_type} (User: {query.user_id})")
    
    # Cosine Identity: Similarity = 1 - Distance
    similarity_expr = 1 - BiomechanicalSignature.embedding.cosine_distance(query.embedding)
    
    stmt = (
        select(BiomechanicalSignature, similarity_expr.label("similarity_score"))
        .where(BiomechanicalSignature.user_id == query.user_id)
        .where(BiomechanicalSignature.movement_type == query.movement_type)
        .order_by(BiomechanicalSignature.embedding.cosine_distance(query.embedding))
        .limit(query.limit)
    )
    
    try:
        result = await db.execute(stmt)
        rows = result.all()
        
        matches = [
            SimilarBiomechanicsResult(
                id=sig.id,
                movement_type=sig.movement_type,
                kinematic_notes=sig.kinematic_notes,
                similarity_score=float(score),
                is_golden=sig.is_golden
            ) for sig, score in rows
        ]
        
        logger.info(f"[InferenceEngine] Found {len(matches)} biomechanical matches.")
        return matches
        
    except Exception as e:
        logger.error(f"[InferenceEngine] Biomechanical similarity search failed: {e}")
        raise
