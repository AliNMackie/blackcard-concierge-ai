"""
Contextual Memory Schema — Level 5: Ambient Physical Intelligence
Database models for continuous inference and biomechanical tracking.

Models:
- InferenceState: Represents the user's rolling situational context.
- BiomechanicalSignature: Stores the user's "Golden Form" and mechanical drift.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.schema import Index

from app.database import Base


class InferenceState(Base):
    """
    Represents a snapshot of the user's continuous situational context.
    Rather than a discrete 'WorkoutLog', this is an ambient state vector.
    
    Vector Dimensions (Embedded via Gemini 3.1 Text Embedding, 768d):
    The textual representation encoded here captures:
      - Physiological strain (HRV deviation, sleep debt)
      - Psychological stress (meeting density, calendar events)
      - Environmental context (travel status, timezone)
    """
    __tablename__ = "inference_states"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    
    # 768-dimensional vector from Gemini embeddings
    state_vector = mapped_column(Vector(768))
    
    # Textual description of the state (e.g. "Slept 5hrs after transatlantic flight, HR elevated")
    context_summary: Mapped[str] = mapped_column(String)
    
    # What happened during this state? (e.g., "Injury", "PR", "Burnout")
    resulting_outcome: Mapped[str] = mapped_column(String, nullable=True)
    
    # Raw JSON of the discrete metrics at this snapshot
    raw_metrics = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # HNSW Index for ultra-fast Approximate Nearest Neighbor search on cosine distance
    __table_args__ = (
        Index(
            "ix_inference_states_vector_hnsw",
            "state_vector",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"state_vector": "vector_cosine_ops"},
        ),
    )


class BiomechanicalSignature(Base):
    """
    Stores the user's "Golden Form" spatial embedding for specific movements.
    Used to calculate mechanical drift from 900-frame video analysis.
    """
    __tablename__ = "biomechanical_signatures"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    
    # 'barbell_squat', 'deadlift', etc.
    movement_type: Mapped[str] = mapped_column(String, index=True)
    
    # Is this their perfect "Golden Form" or a generic historical snapshot?
    is_golden: Mapped[bool] = mapped_column(default=False)
    
    # Spatial/Temporal embedding of the movement pattern (768d)
    embedding = mapped_column(Vector(768))
    
    # Observations from Gemini Vision (e.g., "Slight hip shift at depth")
    kinematic_notes: Mapped[str] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index(
            "ix_biomechanical_signatures_vector_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
