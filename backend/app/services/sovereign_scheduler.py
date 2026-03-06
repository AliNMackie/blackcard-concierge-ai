import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import WorkoutSession, ExerciseLog, EventLog, DailyInsight
from datetime import datetime

logger = logging.getLogger("elite-concierge")

# Heuristic mapping for "Protocol Healing"
# Maps heavy compound movements to corrective/recovery alternatives
HEALING_MAP = {
    "Barbell Squat": {
        "replacement": "Goblet Squat",
        "reason": "Lumbar stability debt detected. Shifting load anteriorly for spinal decompression.",
        "sets_adj": 0,
        "reps_adj": 2, # Increase reps, decrease load
        "weight_factor": 0.4
    },
    "Deadlift": {
        "replacement": "Kettlebell Swings (Light)",
        "reason": "Posterior chain shear risk. Shifting to dynamic hinge with sub-maximal loading.",
        "sets_adj": -1,
        "reps_adj": 5,
        "weight_factor": 0.2
    },
    "Bench Press": {
        "replacement": "Dumbbell Floor Press",
        "reason": "Scapular dyskinesis flagged. Restricting range of motion to protect glenohumeral joint.",
        "sets_adj": 0,
        "reps_adj": 2,
        "weight_factor": 0.6
    },
    "Overhead Press": {
        "replacement": "Landmine Press",
        "reason": "Shoulder impingement risk. Modifying pressing angle for joint clearance.",
        "sets_adj": 0,
        "reps_adj": 0,
        "weight_factor": 0.5
    }
}

class SovereignHealer:
    @staticmethod
    async def heal_protocol(user_id: str, roi_data: Dict[str, Any], db: AsyncSession) -> Optional[Dict[str, Any]]:
        """
        Intervenes autonomously when ROI is RED.
        Mutates the next 'WorkoutSession' by swapping high-risk movements.
        """
        roi_score = roi_data.get("roi_score", 0)
        status = roi_data.get("status", "GREEN")
        
        if status != "RED" or roi_score < 70:
            return None

        logger.info(f"SOVEREIGN INTERVENTION TRIGGERED for User {user_id}. ROI: {roi_score}")

        # 1. Find the next 'planned' workout session (e.g., today's or tomorrow's)
        # For the MVP, we assume a session without 'notes' or 'rpe' is 'planned'
        stmt = (
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user_id)
            .where(WorkoutSession.rpe == None)
            .order_by(WorkoutSession.date.asc())
            .limit(1)
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            logger.warning(f"No upcoming session found for sovereign healing (User: {user_id})")
            return None

        # 2. Iterate through exercises and apply healing map
        mutations = []
        original_protocol = []
        stmt_exercises = select(ExerciseLog).where(ExerciseLog.session_id == session.id)
        res_exercises = await db.execute(stmt_exercises)
        exercises = res_exercises.scalars().all()
        
        for ex in exercises:
            # Capture state for audit ledger
            original_protocol.append({
                "exercise_name": ex.exercise_name,
                "sets": ex.sets,
                "reps": ex.reps,
                "weight_kg": ex.weight_kg
            })

            if ex.exercise_name in HEALING_MAP:
                config = HEALING_MAP[ex.exercise_name]
                old_name = ex.exercise_name
                
                # Apply Mutation
                ex.exercise_name = config["replacement"]
                ex.sets = max(1, ex.sets + config["sets_adj"])
                ex.reps += config["reps_adj"]
                ex.weight_kg = round(ex.weight_kg * config["weight_factor"], 1)
                
                mutations.append({
                    "original": old_name,
                    "replacement": config["replacement"],
                    "reason": config["reason"]
                })

        if mutations:
            # 3. Log to Enterprise Audit Ledger (Phase 5.3)
            from app.core.audit_ledger import audit_ledger
            mutated_protocol = [{
                "exercise_name": ex.exercise_name,
                "sets": ex.sets,
                "reps": ex.reps,
                "weight_kg": ex.weight_kg
            } for ex in exercises]

            await audit_ledger.log_intervention(
                db=db,
                user_id=user_id,
                session_id=session.id,
                biometric_trigger=roi_data,
                original_protocol=original_protocol,
                mutated_protocol=mutated_protocol,
                reasoning=f"Sovereign healing triggered by ROI score {roi_score}. {len(mutations)} exercises mutated."
            )

            # 4. Log the intervention event (Legacy/UI)
            log_entry = EventLog(
                user_id=user_id,
                event_type="sovereign_intervention",
                payload={
                    "session_id": session.id,
                    "roi_score": roi_score,
                    "mutations": mutations
                },
                agent_decision="PROTOCOL_HEALED",
                agent_message=f"Sovereign AI has autonomously mutated your protocol to prevent injury. {len(mutations)} exercises modified."
            )
            db.add(log_entry)
            
            # 5. Commit all changes
            await db.commit()
            return {
                "session_id": session.id,
                "mutations": mutations,
                "summary": log_entry.agent_message
            }
            
        return None

# Singleton instance
sovereign_healer = SovereignHealer()
