import asyncio
import sys
import os

# Add 'backend' to sys.path
# Assuming this script is at backend/scripts/test_brain.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import database
from app.database import init_connection_pool
try:
    from agents.orchestrator import get_workout_plan
except ImportError:
    # Fallback if running from root without package structure
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents"))
    from orchestrator import get_workout_plan

async def test_brain():
    print("--- Elite Concierge AI Brain Test ---")
    
    # 1. Init DB
    await init_connection_pool()
    if not database.async_engine:
         print("DB Connection Failed.")
         return

    # 2. Test Client "Bob" (Seeded with Sleep Score 45 -> Needs Recovery)
    client_id = "auth0|bob"
    print(f"Querying Brain for Client: {client_id}")
    
    try:
        response = await get_workout_plan(client_id)
        print("\n\n=== GEMINI RESPONSE ===\n")
        print(response)
        print("\n=======================\n")
        
        # Simple verification
        if "sleep" in response.lower() or "recovery" in response.lower():
             print("[PASS] AI detected need for Recovery/Sleep logic.")
        else:
             print("[WARN] AI might have missed the Sleep Score context.")
             
        if "push" in response.lower() or "sled" in response.lower() or "cat cow" in response.lower():
             print("[PASS] AI suggested actual exercises (Database Connection Works).")
             
    except Exception as e:
        print(f"Error during Brain Execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_brain())
