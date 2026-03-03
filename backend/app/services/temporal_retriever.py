"""
Temporal pgvector Retrieval Service.

Queries session_analysis using decay-weighted cosine similarity:
    Score = (1 - cosine_distance) * exp(-λ * days_since_session)

This ensures recent sessions are weighted higher than historical ones,
even if the historical session has a slightly better cosine match.
"""
import math
import logging
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rag.retriever import retriever

logger = logging.getLogger("elite-concierge")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_LAMBDA = 0.05       # Decay rate: ~14-day half-life
DEFAULT_TOP_K = 5           # Max results to return
MIN_SIMILARITY = 0.3        # Floor to avoid noise


# ---------------------------------------------------------------------------
# Pydantic V2 Output Models
# ---------------------------------------------------------------------------
class TemporalMatch(BaseModel):
    """A single decay-weighted session match."""
    session_analysis_id: str
    content: str
    raw_similarity: float = Field(description="Raw cosine similarity [0,1]")
    days_ago: float = Field(description="Days since this session was recorded")
    weighted_score: float = Field(description="Similarity × exp(-λ × days_ago)")
    recovery_status: Optional[str] = Field(
        default=None,
        description="Recovery status from DailyBiometrics on that day, if available"
    )


class TemporalRetrievalResult(BaseModel):
    """Envelope for temporal retrieval query results."""
    user_id: str
    query_context: str
    lambda_decay: float
    matches: List[TemporalMatch]
    total_candidates: int = Field(
        description="Total rows evaluated before top-k cutoff"
    )


# ---------------------------------------------------------------------------
# Core Retrieval Function (PostgreSQL + pgvector)
# ---------------------------------------------------------------------------
async def retrieve_temporally_weighted(
    user_id: str,
    current_context: str,
    db: AsyncSession,
    *,
    lambda_decay: float = DEFAULT_LAMBDA,
    top_k: int = DEFAULT_TOP_K,
    min_similarity: float = MIN_SIMILARITY,
    filter_recovery_status: Optional[str] = None,
) -> TemporalRetrievalResult:
    """
    Query session_analysis with temporal-decay-weighted cosine similarity.

    The SQL computes:
        raw_sim   = 1 - (embedding <=> :query_vector)
        days_ago  = EXTRACT(EPOCH FROM (NOW() - ws.date)) / 86400.0
        weighted  = raw_sim * exp(-λ * days_ago)

    Optionally LEFT JOINs daily_biometrics to find the recovery status
    on the day of each session, and can filter to only sessions recorded
    on RED/AMBER days.

    Falls back to a Python-side decay calculation when running against
    non-PostgreSQL backends (e.g., SQLite in tests).
    """
    # 1. Generate the query embedding
    try:
        query_vector = await retriever.get_embedding(current_context)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return TemporalRetrievalResult(
            user_id=user_id,
            query_context=current_context,
            lambda_decay=lambda_decay,
            matches=[],
            total_candidates=0,
        )

    vector_literal = f"[{','.join(str(v) for v in query_vector)}]"

    # 2. Detect backend
    engine_name = db.bind.engine.name if db.bind else "unknown"
    is_postgres = engine_name == "postgresql"

    if is_postgres:
        return await _pg_temporal_query(
            user_id=user_id,
            current_context=current_context,
            vector_literal=vector_literal,
            db=db,
            lambda_decay=lambda_decay,
            top_k=top_k,
            min_similarity=min_similarity,
            filter_recovery_status=filter_recovery_status,
        )
    else:
        # Fallback: fetch all candidates and compute decay in Python
        return await _fallback_temporal_query(
            user_id=user_id,
            current_context=current_context,
            query_vector=query_vector,
            db=db,
            lambda_decay=lambda_decay,
            top_k=top_k,
            min_similarity=min_similarity,
        )


# ---------------------------------------------------------------------------
# PostgreSQL Path (Full SQL with pgvector + exp())
# ---------------------------------------------------------------------------
async def _pg_temporal_query(
    user_id: str,
    current_context: str,
    vector_literal: str,
    db: AsyncSession,
    lambda_decay: float,
    top_k: int,
    min_similarity: float,
    filter_recovery_status: Optional[str],
) -> TemporalRetrievalResult:
    """
    Full PostgreSQL query using pgvector cosine distance operator and
    the built-in exp() function for temporal decay.
    """
    recovery_filter = ""
    if filter_recovery_status:
        recovery_filter = "AND db.recovery_status = :recovery_filter"

    sql = text(f"""
        WITH scored AS (
            SELECT
                sa.id                                       AS sa_id,
                sa.content                                  AS content,
                1 - (sa.embedding <=> :qvec::vector)        AS raw_sim,
                EXTRACT(EPOCH FROM (NOW() - ws.date)) / 86400.0
                                                            AS days_ago,
                (1 - (sa.embedding <=> :qvec::vector))
                    * exp(-1.0 * :lambda * (EXTRACT(EPOCH FROM (NOW() - ws.date)) / 86400.0))
                                                            AS weighted_score,
                db.recovery_status                          AS recovery_status
            FROM session_analysis sa
            JOIN workout_sessions ws ON ws.id = sa.session_id
            LEFT JOIN daily_biometrics db
                ON db.user_id = sa.user_id
                AND DATE(db.date) = DATE(ws.date)
            WHERE sa.user_id = :uid
              AND (1 - (sa.embedding <=> :qvec::vector)) >= :min_sim
              {recovery_filter}
        )
        SELECT sa_id, content, raw_sim, days_ago, weighted_score, recovery_status
        FROM scored
        ORDER BY weighted_score DESC
        LIMIT :topk
    """)

    params = {
        "qvec": vector_literal,
        "uid": user_id,
        "lambda": lambda_decay,
        "min_sim": min_similarity,
        "topk": top_k,
    }
    if filter_recovery_status:
        params["recovery_filter"] = filter_recovery_status

    try:
        result = await db.execute(sql, params)
        rows = result.fetchall()
    except Exception as e:
        logger.error(f"Temporal pgvector query failed: {e}")
        return TemporalRetrievalResult(
            user_id=user_id,
            query_context=current_context,
            lambda_decay=lambda_decay,
            matches=[],
            total_candidates=0,
        )

    matches = [
        TemporalMatch(
            session_analysis_id=row.sa_id,
            content=row.content,
            raw_similarity=round(float(row.raw_sim), 4),
            days_ago=round(float(row.days_ago), 2),
            weighted_score=round(float(row.weighted_score), 4),
            recovery_status=row.recovery_status,
        )
        for row in rows
    ]

    return TemporalRetrievalResult(
        user_id=user_id,
        query_context=current_context,
        lambda_decay=lambda_decay,
        matches=matches,
        total_candidates=len(matches),
    )


# ---------------------------------------------------------------------------
# Fallback Path (Python-side decay — for SQLite / test environments)
# ---------------------------------------------------------------------------
async def _fallback_temporal_query(
    user_id: str,
    current_context: str,
    query_vector: list,
    db: AsyncSession,
    lambda_decay: float,
    top_k: int,
    min_similarity: float,
) -> TemporalRetrievalResult:
    """
    Fallback that loads candidate rows and computes cosine similarity +
    temporal decay in Python. Used for SQLite test environments.
    """
    from sqlalchemy import select
    from app.models import SessionAnalysis, WorkoutSession

    stmt = (
        select(SessionAnalysis, WorkoutSession.date)
        .join(WorkoutSession, WorkoutSession.id == SessionAnalysis.session_id)
        .where(SessionAnalysis.user_id == user_id)
    )

    try:
        result = await db.execute(stmt)
        rows = result.all()
    except Exception as e:
        logger.error(f"Fallback temporal query failed: {e}")
        return TemporalRetrievalResult(
            user_id=user_id,
            query_context=current_context,
            lambda_decay=lambda_decay,
            matches=[],
            total_candidates=0,
        )

    now = datetime.now(timezone.utc)
    scored = []

    for sa, session_date in rows:
        # Cosine similarity (Python fallback)
        raw_sim = _cosine_similarity_python(query_vector, list(sa.embedding))
        if raw_sim < min_similarity:
            continue

        if session_date.tzinfo is None:
            session_date = session_date.replace(tzinfo=timezone.utc)
        days_ago = (now - session_date).total_seconds() / 86400.0
        weighted = raw_sim * math.exp(-lambda_decay * days_ago)

        scored.append(
            TemporalMatch(
                session_analysis_id=sa.id,
                content=sa.content,
                raw_similarity=round(raw_sim, 4),
                days_ago=round(days_ago, 2),
                weighted_score=round(weighted, 4),
                recovery_status=None,
            )
        )

    scored.sort(key=lambda m: m.weighted_score, reverse=True)

    return TemporalRetrievalResult(
        user_id=user_id,
        query_context=current_context,
        lambda_decay=lambda_decay,
        matches=scored[:top_k],
        total_candidates=len(scored),
    )


def _cosine_similarity_python(a: list, b: list) -> float:
    """Pure-Python cosine similarity for test/fallback environments."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
