"""
Agent Swarm API Route — Streaming Multi-Agent Orchestration Endpoint.

Accepts a generic user event payload, kicks off the Supervisor graph,
and streams the agents' internal monologue and final tool calls via NDJSON.
"""
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.auth import get_current_user, AuthenticatedUser
from app.multi_agent_graph import run_swarm, swarm_graph, SwarmResult
from langchain_core.messages import HumanMessage

logger = logging.getLogger("elite-concierge")

router = APIRouter(prefix="/swarm", tags=["Agent Swarm"])


class SwarmTriggerPayload(BaseModel):
    event_type: str = Field(
        description="Type of event: 'biometric_drop', 'workout_complete', 'meal_photo'"
    )
    event_payload: dict = Field(
        default={},
        description="Raw event data (e.g., recovery_status, exercise_name, image_description)"
    )


# ---------------------------------------------------------------------------
# Non-streaming endpoint (simpler, returns final result)
# ---------------------------------------------------------------------------
@router.post("/trigger", response_model=SwarmResult)
async def trigger_swarm(
    payload: SwarmTriggerPayload,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Trigger the multi-agent Supervisor swarm for the authenticated user.
    Returns the complete SwarmResult with all agent traces.
    """
    try:
        result = await run_swarm(
            user_id=current_user.uid,
            event_type=payload.event_type,
            event_payload=payload.event_payload,
        )
        return result

    except Exception as e:
        logger.error(f"[Swarm] Execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Swarm execution failed: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Streaming endpoint (NDJSON — agents' monologue in real-time)
# ---------------------------------------------------------------------------
@router.post("/trigger/stream")
async def trigger_swarm_stream(
    payload: SwarmTriggerPayload,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Trigger the multi-agent Supervisor swarm and stream NDJSON events
    as each node completes. Each line is a JSON object:
      {"node": "supervisor", "scratchpad": [...], "next_agent": "recovery"}
      {"node": "recovery", "output": {...}}
      ...
      {"node": "__end__", "final_output": {...}}
    """
    async def event_generator():
        initial_state = {
            "messages": [
                HumanMessage(
                    content=f"Event: {payload.event_type} — "
                            f"{json.dumps(payload.event_payload, default=str)}"
                )
            ],
            "next_agent": "",
            "user_id": current_user.uid,
            "event_type": payload.event_type,
            "event_payload": payload.event_payload,
            "agent_scratchpad": [],
            "final_output": None,
        }

        try:
            async for event in swarm_graph.astream(initial_state):
                # LangGraph astream yields {node_name: state_update} dicts
                for node_name, state_update in event.items():
                    stream_event = {
                        "node": node_name,
                        "scratchpad": state_update.get("agent_scratchpad", []),
                        "next_agent": state_update.get("next_agent"),
                        "final_output": state_update.get("final_output"),
                    }
                    yield json.dumps(stream_event, default=str) + "\n"

        except Exception as e:
            logger.error(f"[Swarm/Stream] Error: {e}")
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(
        event_generator(),
        media_type="application/x-ndjson",
        headers={"X-Content-Type-Options": "nosniff"},
    )
