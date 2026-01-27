import pytest
from unittest.mock import patch, AsyncMock
from langchain_core.messages import HumanMessage
from app.schema import WearableEvent, VisionEvent

# --- DB Mocking ---
# To test flow without DB, we need to mock 'app.main.get_db' or verify logic in isolation.
# Since these are unit/integration tests for the GRAPH logic primarily, we test app_graph directly,
# bypassing the FastAPI layer which injects the DB.
# However, if we want to confirm the DB call works, we would need to test the FastAPI routes.

@pytest.mark.asyncio
async def test_wearable_graph_flow():
    """
    Verifies that the LangGraph logic works (Graph Isolation).
    Does NOT write to DB.
    """
    with patch('app.graph.gemini_client.generate_content') as mock_gen:
        mock_gen.return_value = "Take a rest day, boss. (Mocked)"
        
        from app.graph import app_graph
        
        wearable_state = {
            "messages": [HumanMessage(content="Test Start")],
            "wearable_data": WearableEvent(device_type="whoop", recovery_score=25),
            "vision_data": None
        }
        
        result = await app_graph.ainvoke(wearable_state)
        response = result.get("final_response")
        
        assert response is not None
        assert response.agent_name == "Biometric Sentry"
        assert response.suggested_action == "RED"

@pytest.mark.asyncio
async def test_vision_graph_flow():
    """
    Verifies Vision Agent graph logic.
    """
    with patch('app.graph.gemini_client.generate_content') as mock_gen:
        mock_gen.return_value = "Hypertrophy Bench Press Plan (Mocked)"
        
        from app.graph import app_graph
        
        vision_state = {
            "messages": [HumanMessage(content="Vision Start")],
            "wearable_data": None,
            "vision_data": VisionEvent(detected_equipment=["Bench", "Barbell"])
        }
        
        result = await app_graph.ainvoke(vision_state)
        response = result.get("final_response")
        
        assert response is not None
        assert response.agent_name == "Vision Agent"
