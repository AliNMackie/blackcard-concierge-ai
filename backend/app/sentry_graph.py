"""
LangGraph Biometric Sentry — Autonomous Proactive Loop.

A 4-node StateGraph that:
  1. Ingests the latest DailyBiometrics for a user.
  2. Evaluates recovery status (RED/AMBER/GREEN).
  3. If RED or AMBER → synthesizes a WorkoutSession mutation via Gemini 3.1 Pro.
  4. Persists the DailyInsight and dispatches a WhatsApp/SMS notification.

This is a *proactive* graph — triggered by cron or manual API call,
not by user interaction. It runs autonomously "on behalf of" the user.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END

from app.graph import gemini_client               # Reuse existing Gemini client
from app.schema import SessionMutation, SentryResult

logger = logging.getLogger("elite-concierge")


# ---------------------------------------------------------------------------
# LangGraph State
# ---------------------------------------------------------------------------
class SentryState(TypedDict):
    user_id: str
    # DB session injected by the caller (not serialisation-safe, local use only)
    _db: object
    # Populated by ingest_node
    biometrics_sleep_score: Optional[int]
    biometrics_recovery_status: Optional[str]
    biometrics_date: Optional[str]
    # Populated by sentry_node
    recovery_status: str                    # RED / AMBER / GREEN
    relevant_history: List[str]             # Summaries from temporal retriever
    recovery_protocol: str                  # RAG-retrieved protocol text
    should_intervene: bool
    # Populated by synthesis_node
    session_mutation: Optional[dict]        # Gemini structured output
    synthesis_headline: Optional[str]
    synthesis_advice: Optional[str]
    # Populated by action_node
    notification_payload: Optional[dict]
    actions_taken: List[str]


# ---------------------------------------------------------------------------
# Node 1: Ingest — Fetch latest biometrics from DB
# ---------------------------------------------------------------------------
async def ingest_node(state: SentryState) -> dict:
    """
    Fetches the most recent DailyBiometrics row for the user.
    Requires a db session passed via the graph's config.
    """
    from sqlalchemy import select
    from app.models import DailyBiometrics

    user_id = state["user_id"]
    logger.info(f"[Sentry/Ingest] Fetching biometrics for user={user_id}")

    # DB session is injected via LangGraph config at invocation time
    db = state.get("_db")
    if not db:
        logger.error("[Sentry/Ingest] No database session available")
        return {
            "biometrics_sleep_score": None,
            "biometrics_recovery_status": None,
            "biometrics_date": None,
        }

    stmt = (
        select(DailyBiometrics)
        .where(DailyBiometrics.user_id == user_id)
        .order_by(DailyBiometrics.date.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    bio = result.scalar_one_or_none()

    if not bio:
        logger.warning(f"[Sentry/Ingest] No biometrics found for user={user_id}")
        return {
            "biometrics_sleep_score": None,
            "biometrics_recovery_status": None,
            "biometrics_date": None,
        }

    logger.info(
        f"[Sentry/Ingest] Found: sleep={bio.sleep_score}, "
        f"status={bio.recovery_status}, date={bio.date}"
    )
    return {
        "biometrics_sleep_score": bio.sleep_score,
        "biometrics_recovery_status": bio.recovery_status,
        "biometrics_date": str(bio.date),
    }


# ---------------------------------------------------------------------------
# Node 2: Sentry — Evaluate status + retrieve context
# ---------------------------------------------------------------------------
async def sentry_node(state: SentryState) -> dict:
    """
    Evaluates recovery status. If RED/AMBER, retrieves relevant history
    via the temporal retriever and recovery protocol via RAG.
    """
    recovery_status = state.get("biometrics_recovery_status") or "GREEN"
    sleep_score = state.get("biometrics_sleep_score") or 100

    logger.info(
        f"[Sentry/Evaluate] status={recovery_status}, sleep={sleep_score}"
    )

    # GREEN → no intervention needed
    if recovery_status == "GREEN" and sleep_score >= 70:
        return {
            "recovery_status": "GREEN",
            "should_intervene": False,
            "relevant_history": [],
            "recovery_protocol": "",
        }

    # --- RED or AMBER: Retrieve context ---
    user_id = state["user_id"]
    db = state.get("_db")

    # 2a. Temporal history retrieval
    history_summaries: List[str] = []
    if db:
        try:
            from app.services.temporal_retriever import retrieve_temporally_weighted
            context_query = (
                f"Recovery: {recovery_status}, Sleep Score: {sleep_score}/100. "
                f"User is fatigued and needs a modified session."
            )
            retrieval_result = await retrieve_temporally_weighted(
                user_id=user_id,
                current_context=context_query,
                db=db,
                filter_recovery_status=recovery_status if recovery_status == "RED" else None,
            )
            history_summaries = [m.content for m in retrieval_result.matches]
        except Exception as e:
            logger.error(f"[Sentry/Evaluate] Temporal retrieval failed: {e}")

    # 2b. Recovery protocol retrieval (from DocumentChunk via RAG)
    protocol_text = ""
    try:
        from rag.retriever import retriever
        tier = "tier_1" if recovery_status == "RED" else "tier_2"
        protocol_text = retriever.retrieve_protocol(
            query=f"recovery protocol {recovery_status.lower()} hrv fatigue",
            tags=["recovery", tier],
        )
    except Exception as e:
        logger.warning(f"[Sentry/Evaluate] Protocol retrieval failed: {e}")
        # Inline fallback from recovery_protocol.md
        if recovery_status == "RED":
            protocol_text = (
                "RED Protocol: Zone 1 only (Walking, Yoga). No heavy lifting. "
                "Hydration: 500ml water + 1g sodium. "
                "Breathwork: 5min Physiological Sighs."
            )
        else:
            protocol_text = (
                "AMBER Protocol: Technical work allowed at 50-60% intensity. "
                "Volume reduced by 50%. Sleep optimization: "
                "Magnesium 400mg + L-Theanine 200mg before bed."
            )

    return {
        "recovery_status": recovery_status,
        "should_intervene": True,
        "relevant_history": history_summaries,
        "recovery_protocol": protocol_text,
    }


# ---------------------------------------------------------------------------
# Node 3: Synthesis — Gemini structured output for session mutation
# ---------------------------------------------------------------------------
MUTATION_JSON_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "headline": {
            "type": "STRING",
            "description": "A punchy, premium headline for the intervention (e.g., 'Recovery Protocol Activated')."
        },
        "advice": {
            "type": "STRING",
            "description": "2-3 sentence proactive guidance in a white-glove, senior tone."
        },
        "original_exercises_replaced": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "List of exercises being removed/swapped."
        },
        "replacement_exercises": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "List of replacement exercises."
        },
        "intensity_cap_percent": {
            "type": "INTEGER",
            "description": "Maximum intensity as a percentage of normal (e.g., 50 for AMBER, 0 for RED)."
        },
        "volume_reduction_percent": {
            "type": "INTEGER",
            "description": "Volume reduction as a percentage (e.g., 50 for AMBER, 100 for RED)."
        },
        "session_type_override": {
            "type": "STRING",
            "description": "Override the session type entirely (e.g., 'mobility', 'zone_1_walk', 'breathwork')."
        },
    },
    "required": [
        "headline", "advice", "original_exercises_replaced",
        "replacement_exercises", "intensity_cap_percent",
        "volume_reduction_percent", "session_type_override",
    ],
}


async def synthesis_node(state: SentryState) -> dict:
    """
    Uses Gemini 3.1 Pro to generate a structured WorkoutSession mutation
    based on recovery status, relevant history, and the recovery protocol.
    """
    if not state.get("should_intervene"):
        return {
            "session_mutation": None,
            "synthesis_headline": None,
            "synthesis_advice": None,
        }

    recovery_status = state["recovery_status"]
    sleep_score = state.get("biometrics_sleep_score", "unknown")
    history = state.get("relevant_history", [])
    protocol = state.get("recovery_protocol", "")

    history_str = "\n".join(history) if history else "No relevant history available."

    prompt = f"""
    You are the 'Blackcard Concierge' — a world-class proactive fitness advisor
    for ultra-high-net-worth individuals. Your tone is premium, direct, and 
    protective of the client's long-term performance.

    SITUATION:
    - Recovery Status: {recovery_status}
    - Sleep Score: {sleep_score}/100
    - The client has NOT yet started their session. You are intervening BEFORE they train.

    RECOVERY PROTOCOL (MANDATORY):
    {protocol}

    RELEVANT PAST SESSIONS (temporally-weighted):
    {history_str}

    YOUR TASK:
    Generate a session mutation that overrides the client's planned workout.
    If RED: Replace ALL heavy lifting with Zone 1 activity (walking, yoga, breathwork).
    If AMBER: Reduce volume by 50%, cap intensity at 60%, keep technical movements only.

    Adhere strictly to the JSON output schema.
    """

    # Use Gemini with structured output if available
    gemini_client._ensure_init()

    if gemini_client.model:
        try:
            from vertexai.generative_models import GenerationConfig
            response = gemini_client.model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=MUTATION_JSON_SCHEMA,
                    temperature=0.2,
                ),
            )
            mutation = json.loads(response.text)
        except Exception as e:
            logger.error(f"[Sentry/Synthesis] Gemini call failed: {e}")
            mutation = _mock_mutation(recovery_status)
    else:
        # Mock fallback for local dev
        mutation = _mock_mutation(recovery_status)

    return {
        "session_mutation": mutation,
        "synthesis_headline": mutation.get("headline", "Intervention Active"),
        "synthesis_advice": mutation.get("advice", ""),
    }


def _mock_mutation(status: str) -> dict:
    """Deterministic mock output for local development."""
    if status == "RED":
        return {
            "headline": "Recovery Protocol Activated",
            "advice": (
                "Your biometrics show significant fatigue. I've replaced today's "
                "session with a restorative protocol. Trust the process — this protects "
                "your performance arc."
            ),
            "original_exercises_replaced": ["Back Squat", "Romanian Deadlift", "Barbell Row"],
            "replacement_exercises": ["Breathwork (5min)", "Zone 1 Walk (20min)", "Yoga Flow (15min)"],
            "intensity_cap_percent": 0,
            "volume_reduction_percent": 100,
            "session_type_override": "recovery_protocol",
        }
    else:
        return {
            "headline": "Adaptive Deload In Effect",
            "advice": (
                "Sleep quality was below optimal. I've preserved your movement patterns "
                "but halved the volume and capped intensity at 60%. Sharp technique today, "
                "not heavy loads."
            ),
            "original_exercises_replaced": ["Heavy Singles", "Max Effort Sets"],
            "replacement_exercises": ["Technical Triples @ 60%", "Tempo Work @ RPE 5"],
            "intensity_cap_percent": 60,
            "volume_reduction_percent": 50,
            "session_type_override": "technical_deload",
        }


# ---------------------------------------------------------------------------
# Node 4: Action — Persist insight + send notification
# ---------------------------------------------------------------------------
async def action_node(state: SentryState) -> dict:
    """
    Persists the DailyInsight to the database and constructs a WhatsApp
    notification payload.
    """
    actions: List[str] = []
    user_id = state["user_id"]
    mutation = state.get("session_mutation")

    if not mutation or not state.get("should_intervene"):
        return {
            "notification_payload": None,
            "actions_taken": ["no_intervention_needed"],
        }

    db = state.get("_db")

    # 4a. Persist DailyInsight
    if db:
        try:
            from app.models import DailyInsight
            insight = DailyInsight(
                user_id=user_id,
                date=datetime.now(timezone.utc),
                insight_headline=mutation.get("headline", "Daily Intervention"),
                actionable_advice=mutation.get("advice", ""),
                suggested_plan_override=mutation,
            )
            db.add(insight)
            
            # Phase 5.1: Sovereign Protocol Mutation (Autonomous Healing)
            # If the Sentry has synthesized a mutation, we apply it to the REAL database session
            if mutation and state.get("recovery_status") in ["RED", "AMBER"]:
                from app.services.sovereign_scheduler import sovereign_healer
                # Mock ROI data for the healer based on recovery status
                roi_mock = {
                    "roi_score": 80 if state["recovery_status"] == "RED" else 50,
                    "status": state["recovery_status"]
                }
                healing_result = await sovereign_healer.heal_protocol(user_id, roi_mock, db)
                if healing_result:
                    actions.append("workout_protocol_autonomously_healed")
                    logger.info(f"[Sentry/Action] Sovereign Healer mutated session {healing_result['session_id']}")

            await db.commit()
            actions.append("daily_insight_persisted")
            logger.info(f"[Sentry/Action] DailyInsight persisted for user={user_id}")
        except Exception as e:
            logger.error(f"[Sentry/Action] Failed to persist insight: {e}")
            actions.append(f"insight_persist_failed: {e}")

    # 4b. Build WhatsApp notification payload
    headline = mutation.get("headline", "Blackcard Concierge")
    advice = mutation.get("advice", "")
    session_override = mutation.get("session_type_override", "modified")

    whatsapp_body = (
        f"🏴 *{headline}*\n\n"
        f"{advice}\n\n"
        f"📋 Today's plan: _{session_override.replace('_', ' ').title()}_\n\n"
        f"Tap to view your adapted session → blackcard.app/dashboard"
    )

    notification_payload = {
        "channel": "whatsapp",
        "to": user_id,  # In production, resolve to phone number
        "body": whatsapp_body,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # 4c. Attempt to send (mock-safe — Twilio config may not exist)
    try:
        from app.messaging import send_whatsapp
        # In production, resolve user_id → phone number from User.profile_data
        # For now, log the payload as the "send"
        logger.info(
            f"[Sentry/Action] WhatsApp payload prepared for user={user_id}: "
            f"{whatsapp_body[:80]}..."
        )
        actions.append("whatsapp_payload_prepared")
    except Exception as e:
        logger.warning(f"[Sentry/Action] WhatsApp send skipped: {e}")
        actions.append("whatsapp_skipped")

    return {
        "notification_payload": notification_payload,
        "actions_taken": actions,
    }


# ---------------------------------------------------------------------------
# Router: Determines whether to intervene or short-circuit
# ---------------------------------------------------------------------------
def sentry_router(state: SentryState):
    """Routes after sentry_node: intervene or end."""
    if state.get("should_intervene"):
        return "synthesis"
    return END


# ---------------------------------------------------------------------------
# Graph Assembly
# ---------------------------------------------------------------------------
sentry_workflow = StateGraph(SentryState)
sentry_workflow.add_node("ingest", ingest_node)
sentry_workflow.add_node("sentry", sentry_node)
sentry_workflow.add_node("synthesis", synthesis_node)
sentry_workflow.add_node("action", action_node)

sentry_workflow.set_entry_point("ingest")
sentry_workflow.add_edge("ingest", "sentry")
sentry_workflow.add_conditional_edges("sentry", sentry_router, {
    "synthesis": "synthesis",
    END: END,
})
sentry_workflow.add_edge("synthesis", "action")
sentry_workflow.add_edge("action", END)

sentry_graph = sentry_workflow.compile()


# ---------------------------------------------------------------------------
# Public API: Run the Sentry for a user
# ---------------------------------------------------------------------------
async def run_sentry_for_user(
    user_id: str,
    db,
) -> SentryResult:
    """
    Execute the full Sentry graph for a given user.
    Returns a SentryResult Pydantic model.
    """
    initial_state: SentryState = {
        "user_id": user_id,
        "_db": db,
        "biometrics_sleep_score": None,
        "biometrics_recovery_status": None,
        "biometrics_date": None,
        "recovery_status": "GREEN",
        "relevant_history": [],
        "recovery_protocol": "",
        "should_intervene": False,
        "session_mutation": None,
        "synthesis_headline": None,
        "synthesis_advice": None,
        "notification_payload": None,
        "actions_taken": [],
    }

    # LangGraph invoke is sync — we run the async nodes via the graph's
    # built-in async support
    final_state = await sentry_graph.ainvoke(initial_state)

    return SentryResult(
        user_id=user_id,
        recovery_status=final_state.get("recovery_status", "GREEN"),
        intervention_triggered=final_state.get("should_intervene", False),
        session_mutation=(
            SessionMutation(**final_state["session_mutation"])
            if final_state.get("session_mutation")
            else None
        ),
        notification_payload=final_state.get("notification_payload"),
        actions_taken=final_state.get("actions_taken", []),
    )
