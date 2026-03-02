from datetime import datetime
import uuid
from typing import Optional
from sqlalchemy import String, DateTime, JSON, ForeignKey, Text, Integer, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String, primary_key=True) # e.g. "auth0|123" or Firebase UID
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True, index=True)
    role: Mapped[str] = mapped_column(String, default="client")  # client, trainer, admin
    trainer_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    profile_data: Mapped[Optional[dict]] = mapped_column(JSON, default={})
    is_traveling: Mapped[bool] = mapped_column(default=False)
    coach_style: Mapped[str] = mapped_column(String, default="hyrox_competitor")
    
    # Billing & Usage
    tier: Mapped[str] = mapped_column(String, default="free") # free, premium, elite
    ai_usage_count: Mapped[int] = mapped_column(Integer, default=0)

    sessions: Mapped[list["WorkoutSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    focus_area: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rpe: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")
    exercises: Mapped[list["ExerciseLog"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    analysis: Mapped[Optional["SessionAnalysis"]] = relationship(back_populates="session", cascade="all, delete-orphan")

class ExerciseLog(Base):
    __tablename__ = "exercise_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, ForeignKey("workout_sessions.id", ondelete="CASCADE"), index=True)
    exercise_name: Mapped[str] = mapped_column(String)
    sets: Mapped[int] = mapped_column(Integer)
    reps: Mapped[int] = mapped_column(Integer)
    weight_kg: Mapped[float] = mapped_column(Float)

    session: Mapped["WorkoutSession"] = relationship(back_populates="exercises")

class SessionAnalysis(Base):
    __tablename__ = "session_analysis"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, ForeignKey("workout_sessions.id", ondelete="CASCADE"), unique=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Vector] = mapped_column(Vector(768))

    session: Mapped["WorkoutSession"] = relationship(back_populates="analysis")

    __table_args__ = (
        Index(
            'hnsw_index_session_analysis',
            embedding,
            postgresql_using='hnsw',
            postgresql_with={'m': 16, 'ef_construction': 64},
            postgresql_ops={'embedding': 'vector_cosine_ops'}
        ),
    )

class EventLog(Base):
    __tablename__ = "events"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=True) # Loose FK for MVP
    event_type: Mapped[str] = mapped_column(String) # "wearable", "vision", "chat"
    
    payload: Mapped[dict] = mapped_column(JSON, default={})
    agent_decision: Mapped[Optional[str]] = mapped_column(String, nullable=True) # "RED", "WORKOUT_GENERATED"
    agent_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    category: Mapped[str] = mapped_column(String) # "Strength", "Hyrox", "Cardio"
    muscle_group: Mapped[str] = mapped_column(String, nullable=True)
    
    # Execution Details
    video_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Logic
    unilateral: Mapped[bool] = mapped_column(default=False)
    equipment: Mapped[dict] = mapped_column(JSON, default=[]) # List of strings

    # Hyrox & Concept2
    is_hyrox_station: Mapped[bool] = mapped_column(default=False)
    concept2_id: Mapped[Optional[int]] = mapped_column(nullable=True)

class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String)
    coach_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True) # Coach who created it
    
    blocks: Mapped[dict] = mapped_column(JSON, default={}) # The actual workout logic

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, index=True)
    category: Mapped[str] = mapped_column(String) # "strength", "engine", "body"
    name: Mapped[str] = mapped_column(String) # "squat", "bench", "weight", "10k"
    value: Mapped[float] = mapped_column()
    unit: Mapped[str] = mapped_column(String) # "kg", "sec", "%"
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logged_by: Mapped[str] = mapped_column(String) # uid of person who logged it
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Vector] = mapped_column(Vector(768)) # Vertex AI 004 dim
    source: Mapped[str] = mapped_column(String)
    tags: Mapped[list] = mapped_column(JSON, default=[]) # Strings
    metadata_json: Mapped[dict] = mapped_column(JSON, default={})
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class DailyBiometrics(Base):
    __tablename__ = "daily_biometrics"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    sleep_score: Mapped[int] = mapped_column(Integer)
    recovery_status: Mapped[str] = mapped_column(String) # RED, AMBER, GREEN

class DailyInsight(Base):
    __tablename__ = "daily_insights"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    insight_headline: Mapped[str] = mapped_column(String)
    actionable_advice: Mapped[str] = mapped_column(Text)
    suggested_plan_override: Mapped[dict] = mapped_column(JSON, default={})

