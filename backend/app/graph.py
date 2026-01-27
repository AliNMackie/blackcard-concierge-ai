import operator
import logging
from typing import TypedDict, Annotated, List, Union

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage

# Vertex AI imports
import vertexai
from vertexai.generative_models import GenerativeModel

# Internal Imports
from app.schema import WearableEvent, VisionEvent, AgentResponse
from rag.retriever import retriever
from app.vision_interface import describe_gym_equipment
from app.config import settings, logger

# Helper: Vertex Client Abstraction
class GeminiClient:
    def __init__(self):
        self.model = None
        if settings.is_production():
            try:
                vertexai.init(project=settings.PROJECT_ID, location=settings.GCP_REGION)
                self.model = GenerativeModel(settings.GEMINI_MODEL_ID)
                logger.info(f"Vertex AI initialized with model: {settings.GEMINI_MODEL_ID}")
            except Exception as e:
                logger.error(f"Vertex AI init failed: {e}")
        else:
            logger.warning("Running in MOCK mode. Vertex AI calls will return placeholder text.")

    def generate_content(self, prompt: str) -> str:
        if not self.model:
            return f"[MOCK_LLM_RESPONSE] Response to: {prompt[:30]}..."
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"LLM Generation Error: {e}")
            return f"[LLM_ERROR] {str(e)}"

# Global instance for easy mocking
gemini_client = GeminiClient()


# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    wearable_data: Union[WearableEvent, None]
    vision_data: Union[VisionEvent, None]
    final_response: Union[AgentResponse, None]
    next_agent: str

# --- Nodes ---

def concierge_node(state: AgentState) -> dict:
    """Router Node"""
    wearable = state.get('wearable_data')
    vision = state.get('vision_data')
    
    logger.info(f"Concierge Routing: Wearable={bool(wearable)}, Vision={bool(vision)}")
    
    if wearable:
        return {"next_agent": "biometric_sentry"}
    elif vision:
        return {"next_agent": "vision_agent"}
    else:
        # Default fallback
        return {
            "next_agent": "END", 
            "final_response": AgentResponse(
                agent_name="Concierge", 
                message="No actionable data found. How can I help?", 
                suggested_action="IDLE"
            )
        }

def biometric_node(state: AgentState) -> dict:
    """Biometric Sentry Node"""
    logger.info("Biometric Sentry: Analysis started")
    data = state['wearable_data']
    
    # Logic
    score = data.recovery_score
    status = "RED" if score < 40 else "AMBER" if score < 70 else "GREEN"
    
    # RAG Retrieval: Using retrieve_protocol interface
    context_docs = ""
    # Retrieve if recovery is low OR if explicit tags are present (future)
    if status in ["RED", "AMBER"]:
        logger.info("Biometric Sentry: Retrieving RAG context")
        # Querying with specific keywords for the retriever's heuristic
        context_docs = retriever.retrieve_protocol(query="recovery low hrv fatigue", tags=["recovery"])
    
    # LLM Gen
    prompt = f"""
    You are an Elite Fitness Concierge for a UHNW client.
    The client's recovery score is {score}/100 (Status: {status}).
    Device: {data.device_type}.
    
    Relevant Framework Context:
    {context_docs}
    
    Draft a short, premium text message.
    """
    
    ai_msg = gemini_client.generate_content(prompt)
    
    return {
        "final_response": AgentResponse(
            agent_name="Biometric Sentry",
            message=ai_msg,
            suggested_action=status
        )
    }

def vision_node(state: AgentState) -> dict:
    """Vision Agent Node"""
    logger.info("Vision Agent: Analysis started")
    data = state['vision_data']
    
    # Analyze image if provided
    detected = data.detected_equipment
    
    # If no structured data is provided, but we have an image URL (or placeholder bytes in real app)
    # We call the vision interface
    if not detected and data.image_url:
        logger.info("Vision Agent: Delegating to Vision Interface")
        # NOTE: In a real scenario, we would download bytes from image_url or use a helper
        # passing b"placeholder" for now to exercise the mock
        analysis = describe_gym_equipment(b"placeholder_bytes") 
        detected = analysis['detected_equipment']

    equip_list = ", ".join(detected) if detected else "Bodyweight only"
    user_q = data.user_query or "Build a workout"
    
    prompt = f"""
    You are an expert Strength Coach.
    Available Equipment: {equip_list}.
    Client Goal/Query: {user_q}.
    
    Create a very brief bulleted workout plan.
    """
    
    ai_msg = gemini_client.generate_content(prompt)
    
    return {
        "final_response": AgentResponse(
            agent_name="Vision Agent",
            message=ai_msg,
            suggested_action="WORKOUT_GENERATED"
        )
    }

# --- Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("concierge", concierge_node)
workflow.add_node("biometric_sentry", biometric_node)
workflow.add_node("vision_agent", vision_node)

workflow.set_entry_point("concierge")

def router(state: AgentState):
    dest = state['next_agent']
    if dest == "END": return END
    return dest

workflow.add_conditional_edges("concierge", router, {"biometric_sentry": "biometric_sentry", "vision_agent": "vision_agent", END: END})
workflow.add_edge("biometric_sentry", END)
workflow.add_edge("vision_agent", END)

app_graph = workflow.compile()
