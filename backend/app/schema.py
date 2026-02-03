from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class WearableEvent(BaseModel):
    device_type: str  # e.g., "oura", "whoop", "apple_watch"
    recovery_score: int
    data: Dict[str, Any] = {}

class VisionEvent(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None # Support for direct uploads
    video_base64: Optional[str] = None # Support for video form checks
    detected_equipment: List[str] = []
    user_query: Optional[str] = None

class ChatEvent(BaseModel):
    user_id: str
    message: str

class AgentResponse(BaseModel):
    agent_name: str
    message: str
    suggested_action: str

class UserUpdate(BaseModel):
    coach_style: Optional[str] = None
    is_traveling: Optional[bool] = None

class MetricCreate(BaseModel):
    category: str # "strength", "engine", "body"
    name: str # e.g. "squat"
    value: float
    unit: str
    timestamp: Optional[datetime] = None
    notes: Optional[str] = None

class MetricResponse(MetricCreate):
    id: str
    user_id: str
    logged_by: str

class StrengthMetric(BaseModel):
    estimated_1rm: float
    exercise: str
    trend: str # "up", "down", "stable"
    history: List[Dict[str, Any]] # Date, Value

class EngineMetric(BaseModel):
    ftp: float # Functional Threshold Power or Pace
    vo2_max: Optional[float]
    history: List[Dict[str, Any]]

class ReadinessMetric(BaseModel):
    score: int # 0-100
    hrv: int
    sleep_score: int
    history: List[Dict[str, Any]]

