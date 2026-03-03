"""
continuous_sentry.py - Level 5 Ambient Intelligence
Maintains a 24-hour sliding window of biometric telemetry.
Autonomously detects anomalies and triggers the LangGraph Supervisor via Contextual Memory inference.
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Any

# Mock Sliding Window Store (In-Memory for now, replace with Redis TimeSeries in production)
# Format: { user_id: [ {timestamp, hr, hrv, stress}, ... ] }
SLIDING_WINDOW: Dict[str, List[Dict]] = {}
WINDOW_DURATION_HOURS = 24

async def process_telemetry_packet(user_id: str, packet: dict, broadcast_callback: Callable):
    """
    Background task triggered by the WebSocket stream.
    Appends data to the sliding window, checks for anomalies, and triggers the swarm.
    """
    now = datetime.utcnow()
    packet['stored_at'] = now
    
    if user_id not in SLIDING_WINDOW:
        SLIDING_WINDOW[user_id] = []
        
    window = SLIDING_WINDOW[user_id]
    window.append(packet)
    
    # Prune old data outside the 24-hour window
    cutoff_time = now - timedelta(hours=WINDOW_DURATION_HOURS)
    SLIDING_WINDOW[user_id] = [p for p in window if p['stored_at'] >= cutoff_time]
    
    # ---------------------------------------------------------
    # Anomaly Detection Logic (e.g., HRV drop during high stress)
    # ---------------------------------------------------------
    is_anomalous = await detect_anomaly(SLIDING_WINDOW[user_id])
    
    if is_anomalous:
        print(f"[SENTRY] Anomaly detected for user {user_id}. Executing Vector Inference...")
        
        # 1. Alert UI Immediately
        await broadcast_callback(user_id, {
            "type": "SENTRY_ALERT",
            "message": "Physiological anomaly detected. Initializing Swarm."
        })
        
        # 2. Construct V_current state_vector
        state_vector = construct_state_vector(SLIDING_WINDOW[user_id])
        
        # 3. Query Inference Engine (Contextual Memory)
        # from app.services.inference_engine import find_similar_situations
        # similarities = await find_similar_situations(SimilarityQuery(user_id=user_id, context_text="Stress Spike"))
        await asyncio.sleep(0.5) # Mock inference delay
        
        # 4. Trigger LangGraph Supervisor (Multi-Agent Swarm)
        # from app.api.routes.agent_swarm import trigger_swarm
        # result = await trigger_swarm(user_id, "biometric_anomaly", {"vector": state_vector})
        await asyncio.sleep(1.0) # Mock swarm routing delay
        
        # 5. Broadcast final ActionDispatch to UI
        await broadcast_callback(user_id, {
            "type": "ACTION_DISPATCH",
            "action": "WORKOUT_RESCHEDULED",
            "payload": {
                "message": "HRV plummeted 15%. Evening lifting session shifted to Active Recovery & Yoga.",
                "new_schedule": "18:00 - Restorative Yoga"
            }
        })


async def detect_anomaly(window: List[Dict]) -> bool:
    """
    Analyzes the sliding window for acute stress markers.
    Returns True if an anomaly is detected.
    """
    if len(window) < 10:
        return False # Need a baseline
        
    latest = window[-1]
    
    # Simple Mock Logic: If stress score > 80 and HRV is suspiciously low
    # In production, this would use a rolling Z-score or Prophet model
    if latest.get("stress_score", 0) > 85 and latest.get("hrv_rmssd_ms", 100) < 30:
        # Prevent spamming triggers by checking if we recently triggered
        if not latest.get("_anomaly_triggered", False):
             latest["_anomaly_triggered"] = True
             return True
             
    return False


def construct_state_vector(window: List[Dict]) -> List[float]:
    """
    Compresses the 24-hour window into a 768-dimensional V_current.
    In reality, we'd feed the window statistics to Gemini to embed, 
    but we mock a 768d numpy array here for structural demonstration.
    """
    # Mock producing a 768-d vector
    vector = np.random.rand(768).tolist()
    return vector
