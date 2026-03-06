import asyncio
import httpx
import time
import random
import uuid
from typing import List

# Configuration
API_URL = "http://localhost:8000/api/v1/biomechanics/audit-edge"
CONCURRENCY = 50
TOTAL_REQUESTS = 200
API_KEY = "DEV_BYPASS_KEY" # Assumed in development environment

async def send_mock_vector(client: httpx.AsyncClient, session_id: str):
    """
    Simulates a 768d vector submission from the edge.
    """
    vector = [random.uniform(-1, 1) for _ in range(768)]
    payload = {
        "session_id": session_id,
        "vector": vector,
        "metadata": {"frame_id": random.randint(1, 1000)}
    }
    
    start_time = time.perf_counter()
    try:
        response = await client.post(
            API_URL, 
            json=payload, 
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=10.0
        )
        end_time = time.perf_counter()
        return end_time - start_time, response.status_code
    except Exception as e:
        return 0, str(e)

async def run_stress_test():
    """
    Orchestrates the concurrent load test.
    """
    print(f"🚀 Starting Stress Test: {TOTAL_REQUESTS} requests with {CONCURRENCY} concurrency...")
    
    async with httpx.AsyncClient() as client:
        tasks = []
        session_id = str(uuid.uuid4())
        
        # We'll reuse few session IDs to simulate concurrent users in sessions
        session_pool = [str(uuid.uuid4()) for _ in range(10)]
        
        for i in range(TOTAL_REQUESTS):
            s_id = random.choice(session_pool)
            tasks.append(send_mock_vector(client, s_id))
            
            if len(tasks) >= CONCURRENCY:
                results = await asyncio.gather(*tasks)
                tasks = []
                # Simple progress report
                print(f"Completed {i+1}/{TOTAL_REQUESTS}...")

    # Analyze Results
    latencies = [r[0] for r in results if isinstance(r[0], float) and r[0] > 0]
    errors = [r[1] for r in results if r[1] != 200 and r[1] != 201]
    
    if latencies:
        avg_lat = sum(latencies) / len(latencies)
        print(f"\n✅ Test Complete!")
        print(f"📊 AVG Latency: {avg_lat*1000:.2f}ms")
        print(f"❌ Errors: {len(errors)}")
    else:
        print("\n❌ Test Failed: No successful requests.")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
