"""
<thinking>
To build the "Ambient" layer, we must model the exact JSON payload streamed from a wearable device (e.g., Apple Watch, Oura, Garmin).
High-frequency telemetry requires lightweight, dense properties.

Expected JSON Payload:
{
    "device_id": "oura_ring_gen3_1234",
    "timestamp": "2026-03-03T14:30:15Z",
    "heart_rate_bpm": 88,
    "hrv_rmssd_ms": 32.5,
    "stress_score": 82,            # 0-100 scale computed by device
    "activity_class": "sedentary", # restful, active, high_intensity
    "skin_temp_delta_c": 0.4
}

The WebSocket will ingest these raw packets, push them to the Sliding Window in the Continuous Sentry, and independently broadcast UI 'ActionDispatch' events downstream to connected clients.
</thinking>
"""

import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
from app.services.continuous_sentry import process_telemetry_packet

router = APIRouter()

# Connection Manager for UI Clients listening to Ambient Sentry Events
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def broadcast_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending to WS: {e}")

manager = ConnectionManager()

@router.websocket("/api/v1/streams/biometrics/{user_id}")
async def wearable_telemetry_stream(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for ingesting high-frequency wearable telemetry 
    AND broadcasting ambient UI updates.
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            # 1. Await incoming UDP-like JSON packet from wearable
            data = await websocket.receive_text()
            try:
                packet = json.loads(data)
                
                # 2. Fire and forget to the Continuous Sentry background task
                # We do not await this deeply, as we want to free the WebSocket loop
                asyncio.create_task(
                    process_telemetry_packet(user_id, packet, manager.broadcast_to_user)
                )

            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON packet"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        print(f"User {user_id} biometric stream disconnected.")
    except Exception as e:
        manager.disconnect(websocket, user_id)
        print(f"WebSocket Error: {e}")
