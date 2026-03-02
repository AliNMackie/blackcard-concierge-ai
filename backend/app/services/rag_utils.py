from datetime import datetime
from typing import List
from app.models import WorkoutSession, ExerciseLog

def generate_session_summary(session: WorkoutSession, logs: List[ExerciseLog]) -> str:
    """
    Converts raw workout session and log data into a natural language summary.
    """
    date_str = session.date.strftime("%B %d, %Y") if session.date else "a recent date"
    focus = session.focus_area if session.focus_area else "general fitness"
    
    summary_parts = [
        f"On {date_str}, the user performed a {focus} session."
    ]
    
    if logs:
        summary_parts.append("Their workout included the following exercises:")
        for log in logs:
            summary_parts.append(
                f"- {log.exercise_name}: {log.weight_kg}kg for {log.sets} sets of {log.reps} reps."
            )
    else:
        summary_parts.append("No specific exercises were logged for this session.")
        
    if session.rpe:
        summary_parts.append(f"The user rated the session difficulty (RPE) as a {session.rpe} out of 10.")
        
    if session.notes:
        summary_parts.append(f"User notes: {session.notes}")
        
    return " ".join(summary_parts)
