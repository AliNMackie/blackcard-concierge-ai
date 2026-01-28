from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Exercise, WorkoutTemplate, User

router = APIRouter(prefix="/workouts", tags=["training"])

# --- Schema for Responses ---
class ExerciseResponse(BaseModel):
    id: str
    name: str
    category: str
    video_url: Optional[str] = None
    is_hyrox: bool

# --- Endpoints ---

@router.get("/exercises", response_model=List[ExerciseResponse])
async def list_exercises(db: AsyncSession = Depends(get_db)):
    """
    Returns all core exercises in the database.
    """
    result = await db.execute(select(Exercise))
    exercises = result.scalars().all()
    
    return [
        ExerciseResponse(
            id=str(ex.id),
            name=ex.name,
            category=ex.category,
            video_url=ex.video_url,
            is_hyrox=ex.is_hyrox_station
        ) for ex in exercises
    ]

@router.get("/demo/{client_id}")
async def get_demo_workout(client_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns a mock/demo workout template based on client ID.
    In a real app, this would query a 'WorkoutAssignment' table.
    """
    # 1. Fetch User to personalize response
    user_result = await db.execute(select(User).where(User.id == client_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        # Fallback for demo if seed hasn't run or using different ID
        user_name = "Client" 
    else:
        user_name = user.profile_data.get("name", "Client")

    # 2. Construct Demo Workout Logic
    # We'll just return a hardcoded structure similar to the seed data for MVP
    # Ideally we fetch a random WorkoutTemplate
    
    # Query specific exercises to build the session
    ex_names = ["Sled Push", "Wall Balls", "Burpee Broad Jump"] 
    # Fallback to defaults if seed data missing
    
    session_exercises = []
    
    try:
        stmt = select(Exercise).where(Exercise.name.in_(ex_names))
        result = await db.execute(stmt)
        db_exercises = result.scalars().all()
        
        # Add basic logic (sets/reps)
        for ex in db_exercises:
             session_exercises.append({
                 "id": str(ex.id),
                 "name": ex.name,
                 "sets": 3,
                 "reps": 10 if ex.category != "Hyrox" else 15, // Hyrox usually higher reps
                 "weight": 0,
                 "video_url": ex.video_url
             })
             
    except Exception as e:
        # If DB empty, empty list
        pass
        
    if not session_exercises:
         # Hard failover if DB not seeded
         session_exercises = [
             {"id": "mock_1", "name": "Mock Push Up", "sets": 3, "reps": 10, "weight": 0}
         ]

    return {
        "id": "demo_session_1",
        "name": f"First Session for {user_name}",
        "exercises": session_exercises
    }

