import json
import logging
from typing import Dict, Any, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

from app.models import SessionAnalysis
from app.config import settings
from rag.retriever import retriever

logger = logging.getLogger("elite-concierge")

# ---------------------------------------------------------
# GEMINI SYNTHESIS ENGINE
# ---------------------------------------------------------

class CoachingEngine:
    def __init__(self):
        self.model = None
        self._initialized = False

    def _ensure_init(self):
        if self._initialized:
            return
            
        if settings.is_production() or True: # Force init for now if possible
            try:
                vertexai.init(
                    project=settings.PROJECT_ID, 
                    location=settings.GCP_REGION,
                )
                # Using Gemini 1.5 Pro or newer per requirements (gemini-3.1-pro if available in GCP project)
                # The user specified 'gemini-3.1-pro' in task.
                self.model = GenerativeModel("gemini-3.1-pro")
                logger.info(f"Coaching Engine initialized with model: gemini-3.1-pro")
            except Exception as e:
                logger.error(f"Vertex AI init failed in CoachingEngine: {e}")
                # Fallback to config default if 3.1-pro fails locally
                try:
                    self.model = GenerativeModel(settings.GEMINI_MODEL_ID)
                except:
                    pass
        else:
            logger.warning("Running CoachingEngine in MOCK mode.")
            
        self._initialized = True


coaching_engine = CoachingEngine()

JSON_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "coaching_cue": {
            "type": "STRING",
            "description": "A short, motivating 2-sentence instruction based on history and feedback."
        },
        "adapted_plan": {
            "type": "OBJECT",
            "description": "The modified workout JSON.",
            "nullable": True
        }
    },
    "required": ["coaching_cue", "adapted_plan"]
}

async def retrieve_relevant_history(user_id: str, current_context: str, db: AsyncSession) -> List[str]:
    """
    Generate an embedding for the current context and retrieve the top 3 most relevant 
    past workout summaries for the user.
    """
    try:
        # Generate embedding for current context (using existing retriever utility)
        query_vector = await retriever.get_embedding(current_context)
        
        # Query SessionAnalysis table using cosine similarity
        bind = db.bind
        
        stmt = select(SessionAnalysis).filter(SessionAnalysis.user_id == user_id)
        
        # pgvector operators ONLY work on PostgreSQL
        if db.bind.engine.name == 'postgresql':
            stmt = stmt.order_by(SessionAnalysis.embedding.cosine_distance(query_vector))
        
        stmt = stmt.limit(3)

        
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        
        summaries = [s.content for s in sessions if s.content]
        return summaries
        
    except Exception as e:
        logger.error(f"Error retrieving history for user {user_id}: {e}")
        return []

async def generate_coach_adaptation(
    user_id: str, 
    current_workout_plan: Dict[str, Any], 
    user_feedback: str, 
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Use RAG-retrieved history and Gemini to generate an adapted workout plan and a coaching cue.
    """
    # 1. Retrieve history
    current_context = f"Current Plan: {json.dumps(current_workout_plan)}. Feedback: {user_feedback}"
    history_summaries = await retrieve_relevant_history(user_id, current_context, db)
    
    history_str = "\n".join(history_summaries) if history_summaries else "No relevant history found."
    
    # 2. Get User State (Injuries, Biometrics, Travel)
    from app.models import User, DailyBiometrics
    
    # Fetch User and latest Biometrics in parallel (or sequential for simplicity in async)
    user_stmt = select(User).where(User.id == user_id)
    bio_stmt = select(DailyBiometrics).where(DailyBiometrics.user_id == user_id).order_by(DailyBiometrics.date.desc()).limit(1)
    
    user_result = await db.execute(user_stmt)
    bio_result = await db.execute(bio_stmt)
    
    user = user_result.scalar_one_or_none()
    latest_bio = bio_result.scalar_one_or_none()
    
    # Construct State Context
    injuries = "None reported"
    if user and user.profile_data:
        injuries = user.profile_data.get("injuries", "None reported")
        
    recovery_status = "Unknown"
    sleep_score = "N/A"
    if latest_bio:
        recovery_status = latest_bio.recovery_status
        sleep_score = str(latest_bio.sleep_score)

    travel_constraint = ""
    if user and user.is_traveling:
        travel_constraint = f"\n- TRAVEL MODE: ACTIVE (Limit equipment to: {user.equipment_constraint})"

    state_context = f"""
    USER STATE CONTEXT:
    - Injury History: {injuries}
    - Recovery Status: {recovery_status}
    - Sleep Score: {sleep_score}
    {travel_constraint}
    """

    # 3. Construct Standardized Prompt
    prompt = f"""
    You are an elite, world-class Personal Trainer AI.
    Your task is to adapt the user's current workout plan based on their immediate feedback, past history, and current physical state.
    
    {state_context}
    
    USER FEEDBACK: "{user_feedback}"
    
    CURRENT WORKOUT PLAN:
    {json.dumps(current_workout_plan, indent=2)}
    
    USER RELEVANT HISTORY (Past Sessions):
    {history_str}
    
    ADAPTATION RULES:
    1. If Recovery Status is 'RED', drastically reduce volume and intensity.
    2. If Injuries are present, ensure no exercises aggravate the listed areas.
    3. If TRAVEL MODE is active, strictly adhere to equipment constraints while maintaining target stimulus.
    
    Generate a highly personalized response. Adhere strictly to the requested JSON schema.
    Provide a 'coaching_cue' (2 sentences max) that is motivating and incorporates insights from history/feedback/state.
    Provide the 'adapted_plan' which is the updated iteration of the current workout plan.
    """

    
    coaching_engine._ensure_init()
    
    if not coaching_engine.model:
        # Mock Response
        return {
            "coaching_cue": "[MOCK] Ensure you brace your core. Let's reduce the weight slightly based on your knee feedback.",
            "adapted_plan": current_workout_plan
        }
        
    try:
        response = coaching_engine.model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                response_mime_type="application/json",
                response_schema=JSON_SCHEMA,
                temperature=0.2
            )
        )
        
        response_json = json.loads(response.text)
        return response_json
        
    except Exception as e:
        logger.error(f"Gemini Adaptation Error: {e}")
        # Send a safe fallback response
        return {
            "coaching_cue": f"I couldn't generate a personalized plan due to a system error. Please proceed carefully with the original plan. Error: {str(e)}",
            "adapted_plan": current_workout_plan
        }
