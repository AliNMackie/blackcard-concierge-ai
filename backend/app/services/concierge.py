import json
import logging
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from vertexai.generative_models import GenerativeModel, GenerationConfig

from app.models import DailyBiometrics, DailyInsight
from app.services.rag_service import retrieve_relevant_history, coaching_engine
from app.config import settings

logger = logging.getLogger("elite-concierge")

# ---------------------------------------------------------
# PROACTIVE CONCIERGE SYNTHESIS
# ---------------------------------------------------------

INSIGHT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "insight_headline": {
            "type": "STRING",
            "description": "A punchy, premium headline for the daily briefing."
        },
        "actionable_advice": {
            "type": "STRING",
            "description": "Proactive guidance based on biometrics and history. Senior, white-glove tone."
        },
        "suggested_plan_override": {
            "type": "OBJECT",
            "description": "Detailed modifications to the standard routine if recovery is suboptimal.",
            "nullable": True
        }
    },
    "required": ["insight_headline", "actionable_advice", "suggested_plan_override"]
}

async def generate_morning_briefing(
    user_id: str, 
    biometrics: DailyBiometrics, 
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Synthesizes current biometrics with past workout history to create a proactive 
    'Morning Briefing' for the elite user.
    """
    # 1. Retrieve history context
    # We query with the recovery status to find relevant past sessions where they felt similar
    current_context = f"Recovery: {biometrics.recovery_status}, Sleep Score: {biometrics.sleep_score}/100"
    history_summaries = await retrieve_relevant_history(user_id, current_context, db)
    history_str = "\n".join(history_summaries) if history_summaries else "No relevant history found."

    # 2. Construct Prompt
    prompt = f"""
    You are the 'Blackcard Concierge' for a ultra-high-net-worth individual. 
    Your tone is world-class, proactive, sophisticated, and direct.
    
    CLIENT BIOMETRICS TODAY:
    - Sleep Score: {biometrics.sleep_score}/100
    - Recovery Status: {biometrics.recovery_status}
    
    CLIENT RELEVANT HISTORY:
    {history_str}
    
    Your mission is to provide a 'Morning Briefing' that anticipates friction.
    If the recovery is RED or AMBER, be protective of their longevity. Suggest exact modifications (e.g. 'swap the heavy squats for mobility and a 2km zone 2 recovery walk').
    If the recovery is GREEN, suggest where they can push for an extra 2-5% 'edge'.
    
    Adhere strictly to the premium persona and the JSON output schema.
    """

    coaching_engine._ensure_init()
    
    if not coaching_engine.model:
        # Mock logic based on persona
        if biometrics.recovery_status == "RED":
            return {
                "insight_headline": "Recovery Protocol Initialized",
                "actionable_advice": "I've reviewed your biometric dip. We're pivoting today to prioritize long-term performance over short-term strain.",
                "suggested_plan_override": {"intensity": "low", "focus": "mobility", "duration_limit": "30m"}
            }
        return {
            "insight_headline": "Optimal Performance Window",
            "actionable_advice": "Your data suggests a peak state. Today is the day to execute the heavy singles we've been prepping for.",
            "suggested_plan_override": None
        }

    try:
        response = coaching_engine.model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                response_mime_type="application/json",
                response_schema=INSIGHT_SCHEMA,
                temperature=0.3
            )
        )
        
        return json.loads(response.text)
        
    except Exception as e:
        logger.error(f"Concierge Synthesis Error: {e}")
        return {
            "insight_headline": "System Calibration in Progress",
            "actionable_advice": "I'm monitoring your data, but my synthesis engine encountered a temporary delay. Proceed with intuitive training.",
            "suggested_plan_override": None
        }
