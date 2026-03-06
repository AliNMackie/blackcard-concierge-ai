import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from app.services.sovereign_scheduler import sovereign_healer
from app.models import WorkoutSession, ExerciseLog, AIInterventionLedger

@pytest.mark.asyncio
async def test_sovereign_healer_swaps_exercise_and_logs_audit():
    """
    Asserts that if ROI is RED, the healer:
    1. Finds the upcoming session.
    2. Swaps 'Barbell Squat' for 'Goblet Squat'.
    3. Records the decision in the AIInterventionLedger.
    """
    mock_db = AsyncMock()
    user_id = "test_user_123"
    session_id = str(uuid.uuid4())
    
    # 1. Mock the upcoming session
    mock_session = WorkoutSession(id=session_id, user_id=user_id, rpe=None)
    
    # 2. Mock the exercises in that session
    mock_exercises = [
        ExerciseLog(
            session_id=session_id, 
            exercise_name="Barbell Squat", 
            sets=3, 
            reps=5, 
            weight_kg=100.0
        ),
        ExerciseLog(
            session_id=session_id, 
            exercise_name="Lateral Raise", 
            sets=3, 
            reps=12, 
            weight_kg=10.0
        )
    ]
    
    # Setup mock_db.execute for the session query and the exercises query
    # We use a side_effect to return different results for different queries
    mock_result_session = MagicMock()
    mock_result_session.scalar_one_or_none.return_value = mock_session
    
    mock_result_exercises = MagicMock()
    mock_result_exercises.scalars.return_value.all.return_value = mock_exercises
    
    mock_db.execute.side_effect = [mock_result_session, mock_result_exercises]

    # 3. Simulate RED ROI data
    roi_data = {
        "roi_score": 85,
        "status": "RED",
        "flagged_deviations": ["lumbar_flexion"]
    }

    # 4. Trigger Healing
    result = await sovereign_healer.heal_protocol(user_id, roi_data, mock_db)

    # 5. Assertions
    assert result is not None
    assert result["session_id"] == session_id
    assert len(result["mutations"]) == 1
    assert result["mutations"][0]["original"] == "Barbell Squat"
    assert result["mutations"][0]["replacement"] == "Goblet Squat"

    # Verify Exercise Mutation
    assert mock_exercises[0].exercise_name == "Goblet Squat"
    assert mock_exercises[0].weight_kg == 40.0 # 100 * 0.4 weight factor
    assert mock_exercises[0].reps == 7 # 5 + 2 reps_adj

    # Verify Audit Ledger Recording
    # Check if a model of type AIInterventionLedger was added to the session
    added_objects = [call.args[0] for call in mock_db.add.call_args_list]
    ledger_entries = [obj for obj in added_objects if isinstance(obj, AIInterventionLedger)]
    
    assert len(ledger_entries) == 1
    assert ledger_entries[0].session_id == session_id
    assert ledger_entries[0].user_id == user_id
    assert ledger_entries[0].biometric_trigger == roi_data
    assert "Goblet Squat" in str(ledger_entries[0].mutated_protocol)

    # Verify commit was called
    mock_db.commit.assert_called()

@pytest.mark.asyncio
async def test_sovereign_healer_ignores_green_roi():
    """
    Asserts that if ROI is GREEN, no mutation occurs.
    """
    mock_db = AsyncMock()
    user_id = "test_user_456"
    roi_data = {"roi_score": 10, "status": "GREEN"}

    result = await sovereign_healer.heal_protocol(user_id, roi_data, mock_db)

    assert result is None
    mock_db.execute.assert_not_called()
    mock_db.commit.assert_not_called()
