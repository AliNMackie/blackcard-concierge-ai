from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.rag_service import generate_coach_adaptation

router = APIRouter(prefix="/api/v1/coach", tags=["Coach"])

class CoachAdaptRequest(BaseModel):
    current_workout_plan: Dict[str, Any]
    user_feedback: str
    user_id: str = "default-user" # Optional/Mocked for this iteration if no auth context is passed

class CoachAdaptResponse(BaseModel):
    coaching_cue: str
    adapted_plan: Dict[str, Any]

@router.post("/adapt", response_model=CoachAdaptResponse)
async def adapt_workout(
    payload: CoachAdaptRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    RAG-powered endpoint that fetches relevant workout history and uses Gemini 
    to dynamically adapt the current workout plan based on user feedback.
    """
    try:
        adaptation = await generate_coach_adaptation(
            user_id=payload.user_id,
            current_workout_plan=payload.current_workout_plan,
            user_feedback=payload.user_feedback,
            db=db
        )
        
        return CoachAdaptResponse(
            coaching_cue=adaptation.get("coaching_cue", "Keep pushing!"),
            adapted_plan=adaptation.get("adapted_plan", payload.current_workout_plan)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
