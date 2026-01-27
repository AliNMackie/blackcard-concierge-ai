from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String, primary_key=True) # e.g. "auth0|123" or phone number
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    profile_data: Mapped[Optional[dict]] = mapped_column(JSON, default={})

class EventLog(Base):
    __tablename__ = "events"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=True) # Loose FK for MVP
    event_type: Mapped[str] = mapped_column(String) # "wearable", "vision", "chat"
    
    payload: Mapped[dict] = mapped_column(JSON, default={})
    agent_decision: Mapped[Optional[str]] = mapped_column(String, nullable=True) # "RED", "WORKOUT_GENERATED"
    agent_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
