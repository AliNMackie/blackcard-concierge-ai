"""
Level 4: Multi-Agent LangGraph Swarm — Autonomous Orchestration.

A Supervisor-routed StateGraph that delegates complex user events
to specialized sub-agents:
  - RecoveryAgent:    HRV drops, sleep issues, acute fatigue
  - PerformanceAgent: Workout completions, plateau detection
  - NutritionAgent:   Meal photo uploads, macro estimation

The Supervisor decides routing via Gemini 3.1 Pro structured output.
After each sub-agent completes, control returns to the Supervisor
for potential multi-hop chaining before terminating with FINISH.

Architecture:
  Entry → Supervisor → [recovery | performance | nutrition | FINISH]
                     ↑____________________________________|
"""
import json
import operator
import logging
from datetime import datetime, timezone
from typing import Annotated, List, Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field

from app.graph import gemini_client

logger = logging.getLogger("elite-concierge")


# ═══════════════════════════════════════════════════════════════════════════
# Tool Schemas (Pydantic V2)
# ═══════════════════════════════════════════════════════════════════════════

class RecoveryProtocolQuery(BaseModel):
    """Input schema for querying pgvector recovery protocols."""
    user_id: str = Field(description="The user to query protocols for")
    recovery_status: str = Field(description="RED or AMBER status code")
    hrv_value: Optional[int] = Field(default=None, description="Current HRV reading")
    sleep_score: Optional[int] = Field(default=None, description="Sleep quality 0-100")


class RecoveryProtocolResult(BaseModel):
    """Output schema from pgvector recovery protocol query."""
    protocols: List[str] = Field(description="Matched recovery protocols")
    confidence: float = Field(description="Match confidence 0-1")
    source_documents: List[str] = Field(description="Source document references")


class PlateauDetectionQuery(BaseModel):
    """Input schema for detecting performance plateaus via vector drift."""
    user_id: str = Field(description="The user to analyze")
    exercise_name: str = Field(default="all", description="Specific exercise or 'all'")
    lookback_days: int = Field(default=30, description="Number of days to analyze")


class PlateauDetectionResult(BaseModel):
    """Output schema from plateau detection via temporal vector drift."""
    is_plateau: bool = Field(description="Whether a plateau is detected")
    drift_score: float = Field(description="Embedding drift magnitude (0=stale, 1=progressing)")
    affected_exercises: List[str] = Field(description="Exercises showing stagnation")
    recommendation: str = Field(description="Suggested periodization change")


class MacroEstimationQuery(BaseModel):
    """Input schema for vision-based macro estimation."""
    image_description: str = Field(description="Description of the meal from vision model")
    meal_type: str = Field(default="unknown", description="breakfast, lunch, dinner, snack")


class MacroEstimationResult(BaseModel):
    """Output schema from macro estimation."""
    calories: int = Field(description="Estimated total calories")
    protein_g: float = Field(description="Estimated protein in grams")
    carbs_g: float = Field(description="Estimated carbohydrates in grams")
    fat_g: float = Field(description="Estimated fat in grams")
    foods_identified: List[str] = Field(description="Individual foods detected")
    confidence: str = Field(description="high, medium, low")


# ═══════════════════════════════════════════════════════════════════════════
# Mock Tool Implementations
# ═══════════════════════════════════════════════════════════════════════════

async def query_pgvector_recovery_protocols(query: RecoveryProtocolQuery) -> RecoveryProtocolResult:
    """
    Mock tool: Queries pgvector for recovery protocols matching the user's
    current biometric state. In production, this would use the temporal
    retriever with decay-weighted cosine similarity.
    """
    logger.info(f"[Tool/Recovery] Querying protocols for status={query.recovery_status}, HRV={query.hrv_value}")

    if query.recovery_status == "RED":
        return RecoveryProtocolResult(
            protocols=[
                "Zone 1 only (Walking, Yoga). No heavy lifting.",
                "Hydration: 500ml water + 1g sodium per hour.",
                "Breathwork: 5min Physiological Sighs.",
                "Sleep Protocol: Magnesium 400mg + L-Theanine 200mg.",
            ],
            confidence=0.92,
            source_documents=["recovery_protocol.md#tier-1", "hrv_optimization.md"],
        )
    else:
        return RecoveryProtocolResult(
            protocols=[
                "Technical work allowed at 50-60% intensity.",
                "Volume reduced by 50%. Focus on movement quality.",
                "Post-session: 20min cold exposure (10-14°C).",
            ],
            confidence=0.85,
            source_documents=["recovery_protocol.md#tier-2"],
        )


async def detect_plateau_via_vector_drift(query: PlateauDetectionQuery) -> PlateauDetectionResult:
    """
    Mock tool: Analyses temporal drift in session embeddings to detect
    performance plateaus. In production, this would compute the cosine
    distance between recent and historical session analysis vectors.
    """
    logger.info(f"[Tool/Performance] Analysing plateau for user={query.user_id}, exercise={query.exercise_name}")

    return PlateauDetectionResult(
        is_plateau=True,
        drift_score=0.12,     # Low drift = stagnation
        affected_exercises=["Barbell Back Squat", "Bench Press"],
        recommendation=(
            "Introduce a 2-week undulating periodization block. "
            "Alternate heavy (3×3 @ 85%) and volume (4×8 @ 65%) days. "
            "Add pause reps to break through the sticking point."
        ),
    )


async def estimate_macros_via_vision(query: MacroEstimationQuery) -> MacroEstimationResult:
    """
    Mock tool: Estimates macronutrients from a meal image description.
    In production, this would use Gemini 3.1 Pro multimodal analysis.
    """
    logger.info(f"[Tool/Nutrition] Estimating macros for meal_type={query.meal_type}")

    return MacroEstimationResult(
        calories=680,
        protein_g=42.0,
        carbs_g=65.0,
        fat_g=22.0,
        foods_identified=["Grilled chicken breast", "Brown rice", "Steamed broccoli", "Olive oil drizzle"],
        confidence="high",
    )


# ═══════════════════════════════════════════════════════════════════════════
# Swarm State
# ═══════════════════════════════════════════════════════════════════════════

class SwarmState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    next_agent: str                        # "recovery" | "performance" | "nutrition" | "FINISH"
    user_id: str
    event_type: str                        # "biometric_drop" | "workout_complete" | "meal_photo"
    event_payload: dict                    # Raw event data
    agent_scratchpad: Annotated[List[str], operator.add]  # Internal monologue
    final_output: Optional[dict]           # Terminal response


# ═══════════════════════════════════════════════════════════════════════════
# Node 1: Supervisor
# ═══════════════════════════════════════════════════════════════════════════

SUPERVISOR_ROUTING_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "next_agent": {
            "type": "STRING",
            "description": "Which agent to delegate to: 'recovery', 'performance', 'nutrition', or 'FINISH' if the task is complete."
        },
        "reasoning": {
            "type": "STRING",
            "description": "Brief explanation of why this routing decision was made."
        }
    },
    "required": ["next_agent", "reasoning"]
}


async def supervisor_node(state: SwarmState) -> dict:
    """
    The Supervisor reads the latest user event and the agent scratchpad,
    then decides which sub-agent to invoke next — or FINISH.
    """
    event_type = state["event_type"]
    event_payload = state.get("event_payload", {})
    scratchpad = state.get("agent_scratchpad", [])

    scratchpad_text = "\n".join(scratchpad) if scratchpad else "No agent has acted yet."

    prompt = f"""
    You are the Blackcard Concierge Supervisor — a meta-orchestrator for a fleet
    of specialized AI agents serving an ultra-high-net-worth fitness client.

    AVAILABLE AGENTS:
    - "recovery":    Handles acute HRV drops, sleep quality issues, fatigue states.
    - "performance": Handles workout completions, plateau detection, periodization.
    - "nutrition":   Handles meal photo uploads, macro estimation, dietary advice.

    CURRENT EVENT:
    - Type: {event_type}
    - Payload: {json.dumps(event_payload, default=str)}

    AGENT SCRATCHPAD (actions taken so far):
    {scratchpad_text}

    DECISION RULES:
    1. If the event clearly maps to one domain, route to that agent.
    2. If the scratchpad shows an agent has already acted AND the situation
       could benefit from a second agent (e.g., recovery + nutrition), route to the next.
    3. If all necessary agents have acted OR the event type is simple, output "FINISH".
    4. Never route to the same agent twice in a row.
    5. For "biometric_drop" events, ALWAYS start with "recovery".
    6. For "workout_complete" events, ALWAYS start with "performance".
    7. For "meal_photo" events, ALWAYS start with "nutrition".

    Output your routing decision as JSON.
    """

    gemini_client._ensure_init()

    if gemini_client.model:
        try:
            from vertexai.generative_models import GenerationConfig
            response = gemini_client.model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=SUPERVISOR_ROUTING_SCHEMA,
                    temperature=0.1,
                ),
            )
            decision = json.loads(response.text)
        except Exception as e:
            logger.error(f"[Supervisor] Gemini routing failed: {e}")
            decision = _mock_supervisor_decision(event_type, scratchpad)
    else:
        decision = _mock_supervisor_decision(event_type, scratchpad)

    next_agent = decision.get("next_agent", "FINISH")
    reasoning = decision.get("reasoning", "")

    logger.info(f"[Supervisor] Routing → {next_agent} | Reason: {reasoning}")

    return {
        "next_agent": next_agent,
        "messages": [AIMessage(content=f"[Supervisor] Routing to: {next_agent}. {reasoning}")],
        "agent_scratchpad": [f"[Supervisor] Routed to {next_agent}: {reasoning}"],
    }


def _mock_supervisor_decision(event_type: str, scratchpad: list) -> dict:
    """Deterministic mock routing for local dev and tests."""
    agents_already_called = []
    for entry in scratchpad:
        for agent_name in ["recovery", "performance", "nutrition"]:
            if f"[{agent_name.title()}Agent]" in entry:
                agents_already_called.append(agent_name)

    if event_type == "biometric_drop":
        if "recovery" not in agents_already_called:
            return {"next_agent": "recovery", "reasoning": "Biometric drop detected — routing to Recovery."}
        elif "nutrition" not in agents_already_called:
            return {"next_agent": "nutrition", "reasoning": "Recovery handled. Checking nutrition for holistic support."}
        else:
            return {"next_agent": "FINISH", "reasoning": "All relevant agents have acted."}

    elif event_type == "workout_complete":
        if "performance" not in agents_already_called:
            return {"next_agent": "performance", "reasoning": "Workout completed — analyzing performance."}
        else:
            return {"next_agent": "FINISH", "reasoning": "Performance analysis complete."}

    elif event_type == "meal_photo":
        if "nutrition" not in agents_already_called:
            return {"next_agent": "nutrition", "reasoning": "Meal photo uploaded — estimating macros."}
        else:
            return {"next_agent": "FINISH", "reasoning": "Nutrition analysis complete."}

    return {"next_agent": "FINISH", "reasoning": "Unknown event type — no agent required."}


# ═══════════════════════════════════════════════════════════════════════════
# Node 2: Recovery Agent
# ═══════════════════════════════════════════════════════════════════════════

async def recovery_agent_node(state: SwarmState) -> dict:
    """
    Activated for acute HRV drops or sleep issues.
    Uses the query_pgvector_recovery_protocols tool.
    """
    payload = state.get("event_payload", {})
    user_id = state["user_id"]

    logger.info(f"[RecoveryAgent] Activated for user={user_id}")

    # 1. Call the recovery protocols tool
    query = RecoveryProtocolQuery(
        user_id=user_id,
        recovery_status=payload.get("recovery_status", "AMBER"),
        hrv_value=payload.get("hrv_value"),
        sleep_score=payload.get("sleep_score"),
    )
    tool_result = await query_pgvector_recovery_protocols(query)

    # 2. Synthesise advice via Gemini
    protocols_text = "\n".join(f"- {p}" for p in tool_result.protocols)
    prompt = f"""
    You are the Recovery Agent for a UHNW fitness client.
    Status: {query.recovery_status}. HRV: {query.hrv_value}. Sleep: {query.sleep_score}/100.

    Retrieved protocols (confidence: {tool_result.confidence}):
    {protocols_text}

    Synthesise a 2-sentence proactive recommendation in a premium, direct tone.
    """

    gemini_client._ensure_init()
    if gemini_client.model:
        try:
            advice = gemini_client.model.generate_content(prompt).text
        except Exception as e:
            logger.error(f"[RecoveryAgent] Gemini failed: {e}")
            advice = _mock_recovery_advice(query.recovery_status)
    else:
        advice = _mock_recovery_advice(query.recovery_status)

    output = {
        "agent": "RecoveryAgent",
        "status": query.recovery_status,
        "protocols": tool_result.protocols,
        "advice": advice,
        "confidence": tool_result.confidence,
    }

    return {
        "messages": [AIMessage(content=f"[RecoveryAgent] {advice}")],
        "agent_scratchpad": [
            f"[RecoveryAgent] Tool: query_pgvector_recovery_protocols → "
            f"{len(tool_result.protocols)} protocols (conf={tool_result.confidence}). "
            f"Advice: {advice[:80]}..."
        ],
        "final_output": output,
    }


def _mock_recovery_advice(status: str) -> str:
    if status == "RED":
        return (
            "Your biometrics indicate significant fatigue. I've activated a full "
            "recovery protocol — Zone 1 movement only, with breathwork and hydration focus."
        )
    return (
        "Sleep quality is below par. I've preserved your training but reduced volume "
        "by 50% and capped intensity at 60%. Focus on technique today."
    )


# ═══════════════════════════════════════════════════════════════════════════
# Node 3: Performance Agent
# ═══════════════════════════════════════════════════════════════════════════

async def performance_agent_node(state: SwarmState) -> dict:
    """
    Activated for workout completion data.
    Uses the detect_plateau_via_vector_drift tool.
    """
    payload = state.get("event_payload", {})
    user_id = state["user_id"]

    logger.info(f"[PerformanceAgent] Activated for user={user_id}")

    # 1. Call the plateau detection tool
    query = PlateauDetectionQuery(
        user_id=user_id,
        exercise_name=payload.get("exercise_name", "all"),
        lookback_days=payload.get("lookback_days", 30),
    )
    tool_result = await detect_plateau_via_vector_drift(query)

    # 2. Synthesise advice via Gemini
    affected = ", ".join(tool_result.affected_exercises)
    prompt = f"""
    You are the Performance Agent for a UHNW fitness client.
    Plateau detected: {tool_result.is_plateau}. Drift score: {tool_result.drift_score}.
    Affected exercises: {affected}.
    Recommendation: {tool_result.recommendation}

    Synthesise a 2-sentence coaching insight in a premium, direct tone.
    Include a specific periodization suggestion.
    """

    gemini_client._ensure_init()
    if gemini_client.model:
        try:
            advice = gemini_client.model.generate_content(prompt).text
        except Exception as e:
            logger.error(f"[PerformanceAgent] Gemini failed: {e}")
            advice = _mock_performance_advice()
    else:
        advice = _mock_performance_advice()

    output = {
        "agent": "PerformanceAgent",
        "is_plateau": tool_result.is_plateau,
        "drift_score": tool_result.drift_score,
        "affected_exercises": tool_result.affected_exercises,
        "advice": advice,
    }

    return {
        "messages": [AIMessage(content=f"[PerformanceAgent] {advice}")],
        "agent_scratchpad": [
            f"[PerformanceAgent] Tool: detect_plateau_via_vector_drift → "
            f"plateau={tool_result.is_plateau}, drift={tool_result.drift_score}. "
            f"Affected: {affected}. Advice: {advice[:80]}..."
        ],
        "final_output": output,
    }


def _mock_performance_advice() -> str:
    return (
        "I've detected stagnation in your squat and bench — your embedding drift "
        "is 0.12 over the last 30 days. Switching to an undulating periodization "
        "block with alternating heavy/volume days will break through."
    )


# ═══════════════════════════════════════════════════════════════════════════
# Node 4: Nutrition Agent
# ═══════════════════════════════════════════════════════════════════════════

async def nutrition_agent_node(state: SwarmState) -> dict:
    """
    Activated when a user uploads a meal photo.
    Uses the estimate_macros_via_vision tool.
    """
    payload = state.get("event_payload", {})
    user_id = state["user_id"]

    logger.info(f"[NutritionAgent] Activated for user={user_id}")

    # 1. Call the macro estimation tool
    query = MacroEstimationQuery(
        image_description=payload.get("image_description", "A meal plate"),
        meal_type=payload.get("meal_type", "unknown"),
    )
    tool_result = await estimate_macros_via_vision(query)

    # 2. Synthesise advice via Gemini
    foods = ", ".join(tool_result.foods_identified)
    prompt = f"""
    You are the Nutrition Agent for a UHNW fitness client.
    Meal type: {query.meal_type}. Foods detected: {foods}.
    Estimated macros: {tool_result.calories} kcal, {tool_result.protein_g}g protein,
    {tool_result.carbs_g}g carbs, {tool_result.fat_g}g fat.
    Confidence: {tool_result.confidence}.

    Synthesise a 2-sentence nutrition insight in a premium, direct tone.
    Comment on protein adequacy relative to a 180g daily target.
    """

    gemini_client._ensure_init()
    if gemini_client.model:
        try:
            advice = gemini_client.model.generate_content(prompt).text
        except Exception as e:
            logger.error(f"[NutritionAgent] Gemini failed: {e}")
            advice = _mock_nutrition_advice(tool_result)
    else:
        advice = _mock_nutrition_advice(tool_result)

    output = {
        "agent": "NutritionAgent",
        "calories": tool_result.calories,
        "protein_g": tool_result.protein_g,
        "carbs_g": tool_result.carbs_g,
        "fat_g": tool_result.fat_g,
        "foods_identified": tool_result.foods_identified,
        "advice": advice,
    }

    return {
        "messages": [AIMessage(content=f"[NutritionAgent] {advice}")],
        "agent_scratchpad": [
            f"[NutritionAgent] Tool: estimate_macros_via_vision → "
            f"{tool_result.calories}kcal, {tool_result.protein_g}g protein. "
            f"Foods: {foods}. Advice: {advice[:80]}..."
        ],
        "final_output": output,
    }


def _mock_nutrition_advice(result: MacroEstimationResult) -> str:
    return (
        f"Solid plate — {result.protein_g}g protein from grilled chicken puts you "
        f"at 23% of your 180g daily target. Consider adding a Greek yoghurt later "
        f"to close the gap."
    )


# ═══════════════════════════════════════════════════════════════════════════
# Router: Conditional Edge from Supervisor
# ═══════════════════════════════════════════════════════════════════════════

def swarm_router(state: SwarmState):
    """Routes from Supervisor to the appropriate sub-agent or END."""
    next_agent = state.get("next_agent", "FINISH")
    if next_agent == "FINISH":
        return END
    return next_agent


# ═══════════════════════════════════════════════════════════════════════════
# Graph Assembly
# ═══════════════════════════════════════════════════════════════════════════

swarm_workflow = StateGraph(SwarmState)

# Add nodes
swarm_workflow.add_node("supervisor", supervisor_node)
swarm_workflow.add_node("recovery", recovery_agent_node)
swarm_workflow.add_node("performance", performance_agent_node)
swarm_workflow.add_node("nutrition", nutrition_agent_node)

# Entry point
swarm_workflow.set_entry_point("supervisor")

# Supervisor → conditional routing to agents or END
swarm_workflow.add_conditional_edges("supervisor", swarm_router, {
    "recovery": "recovery",
    "performance": "performance",
    "nutrition": "nutrition",
    END: END,
})

# Each agent loops back to Supervisor for potential multi-hop
swarm_workflow.add_edge("recovery", "supervisor")
swarm_workflow.add_edge("performance", "supervisor")
swarm_workflow.add_edge("nutrition", "supervisor")

# Compile
swarm_graph = swarm_workflow.compile()


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════

class SwarmResult(BaseModel):
    user_id: str
    event_type: str
    agents_invoked: List[str] = Field(description="Ordered list of agents that acted")
    agent_scratchpad: List[str] = Field(description="Internal monologue log")
    final_output: Optional[dict] = Field(description="Last agent's structured output")


async def run_swarm(
    user_id: str,
    event_type: str,
    event_payload: dict,
) -> SwarmResult:
    """
    Execute the full Swarm graph for a given user event.
    Returns a SwarmResult with the complete agent trace.
    """
    initial_state: SwarmState = {
        "messages": [HumanMessage(content=f"Event: {event_type} — {json.dumps(event_payload, default=str)}")],
        "next_agent": "",
        "user_id": user_id,
        "event_type": event_type,
        "event_payload": event_payload,
        "agent_scratchpad": [],
        "final_output": None,
    }

    final_state = await swarm_graph.ainvoke(initial_state)

    # Extract which agents were invoked from the scratchpad
    agents_invoked = []
    for entry in final_state.get("agent_scratchpad", []):
        for agent_name in ["RecoveryAgent", "PerformanceAgent", "NutritionAgent"]:
            if f"[{agent_name}]" in entry and agent_name not in agents_invoked:
                agents_invoked.append(agent_name)

    return SwarmResult(
        user_id=user_id,
        event_type=event_type,
        agents_invoked=agents_invoked,
        agent_scratchpad=final_state.get("agent_scratchpad", []),
        final_output=final_state.get("final_output"),
    )
