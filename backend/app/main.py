from fastapi import FastAPI, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager
import time
from langchain_core.messages import HumanMessage

from app.schema import WearableEvent, VisionEvent, AgentResponse, ChatEvent
from app.graph import app_graph
from app.config import settings, logger
from app.database import get_db, create_tables, init_connection_pool
from app.models import EventLog
from app.webhooks import router as webhook_router
from fastapi.security import APIKeyHeader
from typing import Optional
import os

# Auth Configuration
API_KEY_NAME = "X-Elite-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Depends(api_key_header)):
    # Simple env-based check for MVP
    expected_key = os.getenv("ELITE_API_KEY", "dev-secret-123")
    if api_key == expected_key:
        return api_key
    # Allow dev mode bypass if env var is explicitly set to "DISABLE"
    if os.getenv("AUTH_MODE") == "DISABLE":
        return "dev-bypass"
    
    raise HTTPException(status_code=403, detail="Invalid or missing API Key")

# CORS
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_connection_pool()
    await create_tables() # Auto-create tables for MVP
    yield
    # Shutdown
    # (Optional) close engine

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, lifespan=lifespan)
app.include_router(webhook_router)

# Enable CORS for local/pwa development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, lock this down
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
async def list_events(limit: int = 50, db: AsyncSession = Depends(get_db), auth: str = Depends(get_api_key)):
    """
    Returns recent events for the Trainer 'God Mode' Dashboard.
    """
    if not db:
        # Mock empty response if no DB
        return []
    
    try:
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
        "messages": [HumanMessage(content=f"Wearable Data: {event.recovery_score}")],
        "wearable_data": event,
        "vision_data": None,
        "next_agent": ""
    }
    
    try:
        result = await app_graph.ainvoke(state)
        response = result["final_response"]
        
        # Persist
        if db:
            log_entry = EventLog(
                user_id="default_user", # Placeholder
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
    
    state = {
        "messages": [HumanMessage(content="Vision Request")],
        "wearable_data": None,
        "vision_data": event,
        "next_agent": ""
    }
    
    try:
        result = await app_graph.ainvoke(state)
        response = result["final_response"]
        
        # Persist
        if db:
            log_entry = EventLog(
                user_id="default_user",
                event_type="vision",
                payload=event.model_dump(),
                agent_decision=response.suggested_action,
                agent_message=response.message
            )
            db.add(log_entry)
            await db.commit()

        return response
    except Exception as e:
        logger.error(f"Error processing vision event: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")

@app.post("/events/chat", response_model=AgentResponse)
async def handle_chat(event: ChatEvent, db: AsyncSession = Depends(get_db)):
    logger.info(f"Event: Chat, User: {event.user_id}")
    
    state = {
        "messages": [HumanMessage(content=event.message)],
        "wearable_data": None,
        "vision_data": None,
        "next_agent": ""
    }
    
    try:
        result = await app_graph.ainvoke(state)
        response = result.get("final_response")
        
        if not response: # Stub handling for Concierge
             response = AgentResponse(
                 agent_name="Concierge",
                 message=f"I received your message: '{event.message}'. Chat capabilities coming soon.",
                 suggested_action="CHAT_ACK"
             )
        
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

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on port 8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
