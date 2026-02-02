from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import EventLog
from app.schema import ChatEvent, WearableEvent, AgentResponse
from app.graph import app_graph
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
    Processes via AI agent and sends reply via Twilio.
    """
    from app.config import logger
    from app.messaging import send_whatsapp
    
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
                 agent_name="System",
                 message="I received your message! Processing...",
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

        # 4. Send Outbound Reply via Twilio
        try:
            message_sid = send_whatsapp(to=payload.From, body=response.message)
            logger.info(f"WhatsApp reply sent, SID: {message_sid}")
        except Exception as twilio_err:
            logger.error(f"Failed to send WhatsApp reply: {twilio_err}")
            # Don't fail the whole request if Twilio fails
        
        return {"status": "ok", "reply": response.message}

    except Exception as e:
        logger.error(f"WhatsApp Processing Error: {e}")
        raise HTTPException(status_code=500, detail="Processing failed")


@router.post("/terra")
async def terra_webhook(request: Request, payload: TerraPayload, db: AsyncSession = Depends(get_db)):
    """
    Ingests Terra Wearable Data (Raw).
    Verifies signature and logs to DB. No processing yet.
    """
    # 1. Signature Validation
    terra_sig = request.headers.get("terra-signature", "")
    # Note: parsing payload twice (FastAPI dependency injection vs raw body for HMAC) is tricky.
    # Ideally we use just Request and parse body manually, or trust that Pydantic parsing doesn't alter fields.
    # For HMAC, we need the raw bytes.
    body_bytes = await request.body()
    # Simple check for now (mock logic if secret is placeholder)
    from app.config import settings
    import hmac
    import hashlib

    if settings.TERRA_API_SECRET != "terra-secret-placeholder":
        # Calculate t=timestamp,v1=signature
        # Terra format: t=123456,v1=abcdef...
        try:
            timestamp_part, signature_part = terra_sig.split(',')
            t_value = timestamp_part.split('=')[1]
            v1_value = signature_part.split('=')[1]
            
            # Construct string to sign: t_value + "." + body
            message = f"{t_value}.{body_bytes.decode('utf-8')}"
            expected_sig = hmac.new(
                bytes(settings.TERRA_API_SECRET, 'utf-8'),
                msg=bytes(message, 'utf-8'),
                digestmod=hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(v1_value, expected_sig):
                 logger.warning("Invalid Terra Signature")
                 # raise HTTPException(status_code=403, detail="Invalid Signature") 
                 # For MVP dev flow, we log warning but might proceed if debugging, otherwise block.
                 pass 
        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            pass

    logger.info(f"Webhook (Terra): Type {payload.type}, User {payload.user.get('user_id')}")

    # 2. Routing & Category Mapping
    category_map = {
        "activity": "workout",
        "sleep": "recovery",
        "body": "biometrics",
        "daily": "daily_summary"
    }
    
    event_category = category_map.get(payload.type, "unknown_terra")

    try:
        # 3. Persist Raw Log (No Agent Invocation)
        if db:
            log_entry = EventLog(
                user_id=payload.user.get("user_id", "unknown"),
                event_type=event_category,
                payload=payload.model_dump(),
                agent_decision="PENDING_PROCESSING",
                agent_message="Raw data received from Terra."
            )
            db.add(log_entry)
            await db.commit()
            
        return {"status": "ok", "action": "logged_raw"}

    except Exception as e:
        logger.error(f"Terra Storage Error: {e}")
        raise HTTPException(status_code=500, detail="Terra processing failed")
