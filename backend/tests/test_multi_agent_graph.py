"""
Tests for Level 4: Multi-Agent LangGraph Swarm.

Validates:
  - Supervisor routing logic (biometric_drop→Recovery, workout_complete→Performance, meal_photo→Nutrition)
  - Individual agent tool execution and structured output
  - Multi-hop chaining (Recovery → Nutrition in a single invocation)
  - FINISH termination
  - Tool Pydantic V2 schema validation
"""
import pytest
from unittest.mock import patch, MagicMock

from app.multi_agent_graph import (
    run_swarm,
    _mock_supervisor_decision,
    query_pgvector_recovery_protocols,
    detect_plateau_via_vector_drift,
    estimate_macros_via_vision,
    RecoveryProtocolQuery,
    PlateauDetectionQuery,
    MacroEstimationQuery,
    SwarmResult,
)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Supervisor Routing Logic (Unit Tests — No LLM, No DB)
# ═══════════════════════════════════════════════════════════════════════════

class TestSupervisorRouting:
    """Test the deterministic mock routing decisions."""

    def test_biometric_drop_routes_to_recovery_first(self):
        decision = _mock_supervisor_decision("biometric_drop", [])
        assert decision["next_agent"] == "recovery"

    def test_biometric_drop_routes_to_nutrition_after_recovery(self):
        # Simulate Recovery already having acted
        scratchpad = ["[RecoveryAgent] Tool: query_pgvector... (conf=0.92)"]
        decision = _mock_supervisor_decision("biometric_drop", scratchpad)
        assert decision["next_agent"] == "nutrition"

    def test_biometric_drop_finishes_after_recovery_and_nutrition(self):
        scratchpad = [
            "[RecoveryAgent] Tool: query_pgvector... (conf=0.92)",
            "[NutritionAgent] Tool: estimate_macros... 680kcal",
        ]
        decision = _mock_supervisor_decision("biometric_drop", scratchpad)
        assert decision["next_agent"] == "FINISH"

    def test_workout_complete_routes_to_performance(self):
        decision = _mock_supervisor_decision("workout_complete", [])
        assert decision["next_agent"] == "performance"

    def test_workout_complete_finishes_after_performance(self):
        scratchpad = ["[PerformanceAgent] Tool: detect_plateau... drift=0.12"]
        decision = _mock_supervisor_decision("workout_complete", scratchpad)
        assert decision["next_agent"] == "FINISH"

    def test_meal_photo_routes_to_nutrition(self):
        decision = _mock_supervisor_decision("meal_photo", [])
        assert decision["next_agent"] == "nutrition"

    def test_unknown_event_finishes_immediately(self):
        decision = _mock_supervisor_decision("unknown_event_type", [])
        assert decision["next_agent"] == "FINISH"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Tool Schema & Execution Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestToolSchemas:
    """Validate Pydantic V2 tool schemas and mock tool outputs."""

    async def test_recovery_protocol_query_schema(self):
        query = RecoveryProtocolQuery(
            user_id="test_user", recovery_status="RED", hrv_value=35, sleep_score=42
        )
        assert query.user_id == "test_user"
        assert query.recovery_status == "RED"

    async def test_recovery_tool_returns_protocols(self):
        query = RecoveryProtocolQuery(user_id="u1", recovery_status="RED")
        result = await query_pgvector_recovery_protocols(query)
        assert len(result.protocols) > 0
        assert result.confidence > 0.8
        assert "recovery_protocol.md" in result.source_documents[0]

    async def test_plateau_detection_tool(self):
        query = PlateauDetectionQuery(user_id="u1", exercise_name="squat")
        result = await detect_plateau_via_vector_drift(query)
        assert result.is_plateau is True
        assert result.drift_score < 0.5      # Low drift = stagnation
        assert len(result.affected_exercises) > 0

    async def test_macro_estimation_tool(self):
        query = MacroEstimationQuery(image_description="Chicken and rice", meal_type="lunch")
        result = await estimate_macros_via_vision(query)
        assert result.calories > 0
        assert result.protein_g > 0
        assert len(result.foods_identified) > 0
        assert result.confidence in ["high", "medium", "low"]


# ═══════════════════════════════════════════════════════════════════════════
# 3. End-to-End Swarm Execution (Mock Gemini)
# ═══════════════════════════════════════════════════════════════════════════

class TestSwarmExecution:
    """Full graph execution with mocked Gemini client."""

    async def test_biometric_drop_invokes_recovery_then_nutrition(self):
        """A biometric_drop should invoke Recovery first, then Nutrition (multi-hop)."""
        with patch("app.multi_agent_graph.gemini_client") as mock_gemini:
            mock_gemini.model = None
            mock_gemini._ensure_init = MagicMock()

            result = await run_swarm(
                user_id="swarm_test_user",
                event_type="biometric_drop",
                event_payload={
                    "recovery_status": "RED",
                    "hrv_value": 32,
                    "sleep_score": 38,
                },
            )

        assert isinstance(result, SwarmResult)
        assert result.event_type == "biometric_drop"
        assert "RecoveryAgent" in result.agents_invoked
        assert "NutritionAgent" in result.agents_invoked
        assert result.final_output is not None
        assert result.final_output["agent"] == "NutritionAgent"

    async def test_workout_complete_invokes_performance_only(self):
        """A workout_complete should invoke Performance agent only."""
        with patch("app.multi_agent_graph.gemini_client") as mock_gemini:
            mock_gemini.model = None
            mock_gemini._ensure_init = MagicMock()

            result = await run_swarm(
                user_id="swarm_test_user",
                event_type="workout_complete",
                event_payload={
                    "exercise_name": "squat",
                    "lookback_days": 30,
                },
            )

        assert isinstance(result, SwarmResult)
        assert "PerformanceAgent" in result.agents_invoked
        assert result.final_output["agent"] == "PerformanceAgent"
        assert result.final_output["is_plateau"] is True
        assert result.final_output["drift_score"] == 0.12

    async def test_meal_photo_invokes_nutrition_only(self):
        """A meal_photo should invoke Nutrition agent only."""
        with patch("app.multi_agent_graph.gemini_client") as mock_gemini:
            mock_gemini.model = None
            mock_gemini._ensure_init = MagicMock()

            result = await run_swarm(
                user_id="swarm_test_user",
                event_type="meal_photo",
                event_payload={
                    "image_description": "Grilled salmon with quinoa",
                    "meal_type": "dinner",
                },
            )

        assert isinstance(result, SwarmResult)
        assert "NutritionAgent" in result.agents_invoked
        assert result.final_output["agent"] == "NutritionAgent"
        assert result.final_output["calories"] > 0

    async def test_unknown_event_finishes_with_no_agents(self):
        """An unknown event type should FINISH immediately without invoking sub-agents."""
        with patch("app.multi_agent_graph.gemini_client") as mock_gemini:
            mock_gemini.model = None
            mock_gemini._ensure_init = MagicMock()

            result = await run_swarm(
                user_id="swarm_test_user",
                event_type="random_event",
                event_payload={},
            )

        assert isinstance(result, SwarmResult)
        assert len(result.agents_invoked) == 0

    async def test_scratchpad_accumulates_across_agents(self):
        """The agent_scratchpad should grow as each agent appends its trace."""
        with patch("app.multi_agent_graph.gemini_client") as mock_gemini:
            mock_gemini.model = None
            mock_gemini._ensure_init = MagicMock()

            result = await run_swarm(
                user_id="swarm_test_user",
                event_type="biometric_drop",
                event_payload={"recovery_status": "RED"},
            )

        # Multi-hop: Supervisor → Recovery → Supervisor → Nutrition → Supervisor
        # Expect scratchpad entries from Supervisor (×3) + Recovery + Nutrition
        assert len(result.agent_scratchpad) >= 4
        # Verify ordering: Recovery came before Nutrition
        recovery_idx = next(i for i, s in enumerate(result.agent_scratchpad) if "[RecoveryAgent]" in s)
        nutrition_idx = next(i for i, s in enumerate(result.agent_scratchpad) if "[NutritionAgent]" in s)
        assert recovery_idx < nutrition_idx
