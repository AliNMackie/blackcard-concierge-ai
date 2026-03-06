import json
import logging
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from vertexai.generative_models import GenerativeModel, GenerationConfig

from app.models import User, DailyBiometrics, DailyInsight

from app.services.rag_service import retrieve_relevant_history, coaching_engine
from app.config import settings

logger = logging.getLogger("elite-concierge")

# ---------------------------------------------------------
# PROACTIVE CONCIERGE SYNTHESIS
# ---------------------------------------------------------

from app.services.proactive_sentry import calculate_roi_score

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
        "risk_of_injury_score": {
            "type": "NUMBER",
            "description": "A score from 0 to 100 indicating mechanical drift risk."
        },
        "mechanical_flags": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Specific joints or movements showing kinematic drift."
        },
        "suggested_plan_override": {
            "type": "OBJECT",
            "description": "Detailed modifications to the standard routine if recovery is suboptimal.",
            "nullable": True
        }
    },
    "required": ["insight_headline", "actionable_advice", "risk_of_injury_score", "mechanical_flags", "suggested_plan_override"]
}

async def generate_morning_briefing(
    user_id: str, 
    biometrics: DailyBiometrics, 
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Synthesizes current biometrics with past workout history and predictive 
    kinematic drift to create a proactive 'Morning Briefing'.
    """
    # 1. Retrieve history context
    current_context = f"Recovery: {biometrics.recovery_status}, Sleep Score: {biometrics.sleep_score}/100"
    history_summaries = await retrieve_relevant_history(user_id, current_context, db)
    history_str = "\n".join(history_summaries) if history_summaries else "No relevant history found."

    # 2. Add Predictive Sentry Data (ROI)
    # We focus on their primary baseline movement (e.g., 'Deadlift' for most elite clients)
    roi_data = await calculate_roi_score(user_id, "Deadlift", db)
    
    roi_context = f"""
    PREDICTIVE SENTRY ALERT:
    - Drift Risk Score: {roi_data['roi_score']}/100 ({roi_data['status']})
    - Magnitude: {roi_data.get('drift_magnitude')}
    - Mechanical Flags: {', '.join(roi_data['flagged_deviations']) if roi_data['flagged_deviations'] else 'None'}
    """

    # 3. Get User State (Travel)
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    travel_constraint = ""
    if user and user.is_traveling:
        travel_constraint = f"\nTRAVEL MODE ACTIVE: Client restricted to: {user.equipment_constraint}."

    # 4. Sovereign Autonomous Intervention (Closed-Loop)
    from app.services.sovereign_scheduler import sovereign_healer
    healing_summary = ""
    if roi_data.get("status") == "RED":
        intervention = await sovereign_healer.heal_protocol(user_id, roi_data, db)
        if intervention:
            healing_summary = f"\nSOVEREIGN AI INTERVENTION: This client's upcoming session has been AUTONOMOUSLY mutated. {intervention['summary']}"

    # 5. Personality Logic (Phase 6.1: Persona Cloning)
    from app.services.persona_engine import persona_engine
    voice_signature = "Sophisticated, White-Glove, Predictive."
    if user and user.trainer_id:
        custom_signature = await persona_engine.get_persona_signature(user.trainer_id, db)
        if custom_signature:
            voice_signature = custom_signature

    # 6. Construct Prompt
    prompt = f"""
    PERSONALITY: {voice_signature}
    {travel_constraint}
    
    CURRENT STATE:
    - Recovery: {biometrics.recovery_status} (Sleep: {biometrics.sleep_score})
    {roi_context}
    {healing_summary}
    
    RELEVANT HISTORY:
    {history_str}
    
    Mission: Provide a 'Morning Briefing'. If ROI Risk is RED/AMBER, you MUST prioritize 
    mechanical stability and technical cues to correct the flagged deviations.
    If a SOVEREIGN AI INTERVENTION occurred, explain clearly why we did it and how it protects the client.
    """

    coaching_engine._ensure_init()
    if not coaching_engine.model:
        return {
            "insight_headline": "Optimal Recovery Pipeline",
            "actionable_advice": "Biometrics are stable. Predictive sentry shows nominal drift." + (f" {healing_summary}" if healing_summary else ""),
            "risk_of_injury_score": roi_data['roi_score'],
            "mechanical_flags": roi_data['flagged_deviations'],
            "suggested_plan_override": None
        }

    try:
        response = coaching_engine.model.generate_content(
            prompt,
            # ... (rest of generation config)
            # ... (rest of generation config)
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
            "insight_headline": "Synthesis Recalibration",
            "actionable_advice": "Manual oversight recommended.",
            "risk_of_injury_score": roi_data['roi_score'],
            "mechanical_flags": roi_data['flagged_deviations'],
            "suggested_plan_override": None
        }
