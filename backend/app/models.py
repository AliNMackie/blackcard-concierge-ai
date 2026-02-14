from datetime import datetime
import uuid
from typing import Optional
from sqlalchemy import String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
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

from pgvector.sqlalchemy import Vector

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Vector] = mapped_column(Vector(768)) # Vertex AI 004 dim
    source: Mapped[str] = mapped_column(String)
    tags: Mapped[list] = mapped_column(JSON, default=[]) # Strings
    metadata_json: Mapped[dict] = mapped_column(JSON, default={})
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
