from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import EventLog
from app.schema import ChatEvent, WearableEvent, AgentResponse
from app.graph import app_graph
from app.config import logger
from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/webhooks", tags=["integrations"])

# --- Models for Webhook Payloads ---

class WhatsAppPayload(BaseModel):
    From: str
    Body: str
    Timestamp: Optional[str] = None

class TerraPayload(BaseModel):
    type: str # 'daily', 'activity', etc
    user: Dict[str, Any]
    data: list[Dict[str, Any]]

# --- Endpoints ---

@router.post("/whatsapp")
async def whatsapp_webhook(payload: WhatsAppPayload, db: AsyncSession = Depends(get_db)):
    """
    Ingests WhatsApp messages (mocked as JSON for MVP).
    TODO: Add X-Twilio-Signature verification.
    """
    logger.info(f"Webhook (WhatsApp): From {payload.From}, Msg: {payload.Body[:20]}...")

    # 1. Map to Internal Event
    chat_event = ChatEvent(
        user_id=payload.From,
        message=payload.Body
    )

    # 2. Invoke Agent (Concierge)
    state = {
        "messages": [HumanMessage(content=chat_event.message)],
        "wearable_data": None,
        "vision_data": None,
        "next_agent": ""
    }

    try:
        result = await app_graph.ainvoke(state)
        response = result.get("final_response")
        
        # Fallback if agent returns None
        if not response:
             response = AgentResponse(
                 agent_name="Concierge",
                 message="Received. Processing your request.",
                 suggested_action="ACK"
             )

        # 3. Persist Log
        if db:
            log_entry = EventLog(
                user_id=chat_event.user_id,
                event_type="chat", # captured as chat
                payload=payload.model_dump(),
                agent_decision=response.suggested_action,
                agent_message=response.message
            )
            db.add(log_entry)
            await db.commit()

        # TODO: Send Outbound Reply via Twilio API
        # client.messages.create(body=response.message, from_=..., to=payload.From)
        
        return {"status": "ok", "reply": response.message}

    except Exception as e:
        logger.error(f"WhatsApp Processing Error: {e}")
        raise HTTPException(status_code=500, detail="Processing failed")


@router.post("/terra")
async def terra_webhook(payload: TerraPayload, db: AsyncSession = Depends(get_db)):
    """
    Ingests Terra Wearable Data.
    TODO: Add t-signature verification.
    """
    logger.info(f"Webhook (Terra): Type {payload.type}, User {payload.user.get('user_id')}")

    if payload.type not in ['daily', 'activity', 'sleep']:
        return {"status": "ignored", "reason": f"Type {payload.type} not relevant"}

    try:
        # 1. Extract Data (Simplified for MVP)
        # Terra structures are deep; we look for the first data point
        if not payload.data:
             return {"status": "ignored", "reason": "No data points"}
             
        data_point = payload.data[0]
        scores = data_point.get("scores", {})
        device = data_point.get("device_data", {})
        
        recovery = scores.get("recovery") or scores.get("readiness") or 0
        
        # 2. Map to Internal Event
        wearable_event = WearableEvent(
             device_type=device.get("name", "Unknown Device"),
             recovery_score=int(recovery),
             data=data_point
        )
        
        logger.info(f"Terra Mapped: Device={wearable_event.device_type}, Recovery={wearable_event.recovery_score}")

        # 3. Invoke Agent (Biometric Sentry)
        state = {
            "messages": [HumanMessage(content=f"Incoming Wearable Data: Score {wearable_event.recovery_score}")],
            "wearable_data": wearable_event,
            "vision_data": None,
            "next_agent": ""
        }
        
        result = await app_graph.ainvoke(state)
        response = result.get("final_response")

        if not response:
             return {"status": "ok", "action": "None"}

        # 4. Persist
        if db:
            log_entry = EventLog(
                user_id=payload.user.get("user_id"),
                event_type="wearable",
                payload=payload.model_dump(),
                agent_decision=response.suggested_action,
                agent_message=response.message
            )
            db.add(log_entry)
            await db.commit()
            
        return {"status": "ok", "action": response.suggested_action}

    except Exception as e:
        logger.error(f"Terra Processing Error: {e}")
        # Webhooks should generally return 200/202 to prevent provider retries on logic errors,
        # but for debugging we raise 500
        raise HTTPException(status_code=500, detail="Terra processing failed")
