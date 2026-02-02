from fastapi import FastAPI, Depends, HTTPException, Security, Request, status
from fastapi.security import APIKeyHeader
from app.config import settings, logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from contextlib import asynccontextmanager
from datetime import datetime
import time
from langchain_core.messages import HumanMessage
import os
from app.webhooks import router as webhook_router
from app.workouts import router as workout_router
from app.users import router as users_router, get_trainer_client_ids
from app.database import get_db, init_connection_pool, create_tables
from app.models import User, EventLog
from app.schema import AgentResponse, WearableEvent, VisionEvent, ChatEvent, UserUpdate
from app.auth import get_current_user, get_current_user_optional, AuthenticatedUser, require_trainer, require_admin
# AI Graph
from app.graph import app_graph

# Auth Configuration
API_KEY_NAME = "X-Elite-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Depends(api_key_header)):
    # Simple env-based check for MVP
    primary_key = os.getenv("ELITE_API_KEY")
    
    if primary_key and api_key == primary_key:
        return api_key
        
    # Security: Fallback to development mode is only allowed if ENV is explicitly set to development
    if settings.ENV == "development" and os.getenv("AUTH_MODE") == "DISABLE": 
        logger.warning("AUTH_MODE is DISABLE. Bypassing security in development.")
        return "dev-bypass"
    
    logger.error(f"Auth Failed: Received key '{api_key[:4] if api_key else 'None'}...'")
    raise HTTPException(status_code=403, detail="Invalid or missing API Key")

# CORS
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await init_connection_pool()
        await create_tables() # Auto-create tables for MVP
        logger.info("Startup complete: DB connected and tables verified.")
    except Exception as e:
        logger.critical(f"CRITICAL STARTUP ERROR: {e}")
        # We don't re-raise here to allow the container to start and emit logs, 
        # otherwise Cloud Run kills it instantly, hiding the error.
        
    yield
    # Shutdown
    # (Optional) close engine

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, lifespan=lifespan)
app.include_router(webhook_router)
app.include_router(workout_router)
app.include_router(users_router)

# Enable CORS for local/pwa development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Wildcard for MVP to ensure Netlify connectivity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Path: {request.url.path} Method: {request.method} Status: {response.status_code} Duration: {process_time:.4f}s")
    return response

@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.VERSION}

@app.get("/events")
async def list_events(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Returns recent events for the Trainer 'God Mode' Dashboard.
    If authenticated as trainer, only shows events from their assigned clients.
    """
    if not db:
        # Mock empty response if no DB
        return []
    
    try:
        # Filter by trainer's clients if trainer role
        if current_user and current_user.is_trainer and not current_user.is_admin:
            client_ids = await get_trainer_client_ids(db, current_user.uid)
            if not client_ids:
                return []  # No clients assigned yet
            stmt = select(EventLog).where(EventLog.user_id.in_(client_ids)).order_by(EventLog.created_at.desc()).limit(limit)
        else:
            # Admin or unauthenticated (dev mode) sees all
            stmt = select(EventLog).order_by(EventLog.created_at.desc()).limit(limit)
        
        result = await db.execute(stmt)
        events = result.scalars().all()
        return events
    except Exception as e:
         logger.error(f"Error listing events: {e}")
         raise HTTPException(status_code=500, detail="Database query failed")

@app.post("/events/wearable", response_model=AgentResponse)
async def handle_wearable(event: WearableEvent, db: AsyncSession = Depends(get_db)):
    logger.info(f"Event: Wearable, Device: {event.device_type}, Score: {event.recovery_score}")
    
    # Run Agent
    state = {
        "messages": [],
        "wearable_data": event,
        "vision_data": None,
        "next_agent": ""
    }
    
    try:
        result = await app_graph.ainvoke(state)
        response = result.get("final_response")
        
        if not response:
             response = AgentResponse(agent_name="System", message="Processing completed.", suggested_action="LOGGED")

        # Persist
        if db:
            log_entry = EventLog(
                user_id="1", # Linked to Demo Client (User 1) for dashboard visibility
                event_type="wearable",
                payload=event.model_dump(),
                agent_decision=response.suggested_action,
                agent_message=response.message
            )
            db.add(log_entry)
            await db.commit()
            
        return response
    except Exception as e:
        logger.error(f"Error processing wearable event: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")

@app.post("/events/vision", response_model=AgentResponse)
async def handle_vision(event: VisionEvent, db: AsyncSession = Depends(get_db)):
    logger.info(f"Event: Vision, Equipment Count: {len(event.detected_equipment)}")
    
    # Run Agent
    state = {
        "messages": [],
        "wearable_data": None,
        "vision_data": event,
        "next_agent": ""
    }

    try:
        result = await app_graph.ainvoke(state)
        response = result.get("final_response")
        
        if not response:
             response = AgentResponse(agent_name="System", message="Processing completed.", suggested_action="LOGGED")
        
        # Persist
        if db:
            log_entry = EventLog(
                user_id="1", # Demo Client
                event_type="vision",
                payload=sanitize_payload(event.model_dump()),
                agent_decision=response.suggested_action,
                agent_message=response.message
            )
            # Ensure User 1 exists for vision logging too
            stmt = select(User).where(User.id == "1")
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                db.add(User(id="1", role="client"))

            db.add(log_entry)
            await db.commit()

        return response
    except Exception as e:
        logger.error(f"Error processing vision event: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")

def sanitize_payload(payload: dict) -> dict:
    """
    GDPR Helper: Removes sensitive raw biometric data (images/video) from logs.
    """
    safe_payload = payload.copy()
    if "image_base64" in safe_payload and safe_payload["image_base64"]:
        safe_payload["image_base64"] = "[REDACTED_GDPR_MEDIA]"
    if "video_base64" in safe_payload and safe_payload["video_base64"]:
        safe_payload["video_base64"] = "[REDACTED_GDPR_MEDIA]"
    return safe_payload

@app.delete("/users/{user_id}/wipe")
async def wipe_user_data(user_id: str, db: AsyncSession = Depends(get_db), auth: str = Depends(get_api_key)):
    """
    GDPR: Right to be Forgotten. Permanently deletes all user logs and data.
    """
    try:
        # Delete Event Logs
        stmt_logs = delete(EventLog).where(EventLog.user_id == user_id)
        await db.execute(stmt_logs)
        
        # Reset User Profile (instead of delete, to keep the account shell but wipe personalization)
        # Note: In a real app we might delete the User row too, but for this MVP we reset.
        stmt_user = select(User).where(User.id == user_id)
        result = await db.execute(stmt_user)
        user = result.scalar_one_or_none()
        
        if user:
            user.coach_style = "standard"
            user.is_traveling = False
            # Wipe any other sensitive fields here
        
        await db.commit()
        logger.info(f"GDPR WIPE COMPLETED for User {user_id}")
        return {"status": "success", "message": "All user data scrubbed."}
        
    except Exception as e:
        logger.error(f"GDPR Wipe Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to wipe data")

@app.post("/events/chat", response_model=AgentResponse)
async def handle_chat(event: ChatEvent, db: AsyncSession = Depends(get_db)):
    logger.info(f"Event: Chat, User: {event.user_id}")
    
    # Run Agent
    state = {
        "messages": [HumanMessage(content=event.message)],
        "wearable_data": None,
        "vision_data": None,
        "next_agent": ""
    }

    try:
        result = await app_graph.ainvoke(state)
        response = result.get("final_response")
        
        if not response:
             response = AgentResponse(agent_name="System", message="I heard you, but I'm thinking.", suggested_action="ACK")
        
        # Persist
        if db:
            log_entry = EventLog(
                user_id=event.user_id,
                event_type="chat",
                payload=event.model_dump(),
                agent_decision=response.suggested_action,
                agent_message=response.message
            )
            db.add(log_entry)
            await db.commit()

        return response
    except Exception as e:
        logger.error(f"Error processing chat event: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")

    return user

@app.post("/events/intervention/{client_id}")
async def trigger_intervention(client_id: str, db: AsyncSession = Depends(get_db)):
    """
    Manually triggers the Ghostwriter to generate an intervention based on client context.
    """
    try:
        # 1. Run Brain (Manual Intervention Trigger)
        # We simulate a "System Instruction" to the Concierge/Orchestrator
        state = {
            "messages": [HumanMessage(content=f"Generate a motivational intervention for client {client_id}. They might be slacking.")],
            "wearable_data": None,
            "vision_data": None,
            "next_agent": ""
        }
        
        result = await app_graph.ainvoke(state)
        response = result.get("final_response")
        
        ai_msg = response.message if response else "Intervention generated."
        decision = response.suggested_action if response else "MANUAL_INTERVENTION"
        
        # 3. Persist to Log
        if db:
            log_entry = EventLog(
                user_id=client_id,
                event_type="intervention",
                payload={"trigger": "manual_trainer_intervention"},
                agent_decision=decision,
                agent_message=ai_msg
            )
            db.add(log_entry)
            await db.commit()
            
        return {"status": "ok", "message": ai_msg, "decision": decision}
    except Exception as e:
        logger.error(f"Intervention Trigger Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on port 8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
