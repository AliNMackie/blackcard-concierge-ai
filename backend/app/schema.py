from typing import List, Optional, Dict, Any
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
