from typing import List, Optional, TypedDict

class GymEquipmentDescription(TypedDict):
    detected_equipment: List[str]
    confidence_score: float

import json
import base64
from app.config import settings, logger

# Vertex AI (Lazy import to avoid startup crash if env vars missing in dev)
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part, Image
except ImportError:
    vertexai = None

def describe_gym_equipment(image_bytes: Optional[bytes]) -> GymEquipmentDescription:
    """
    Analyzes gym image using Gemini Vision to detect equipment.
    """
    if not image_bytes:
        return GymEquipmentDescription(detected_equipment=[], confidence_score=0.0)

    # Mock Mode if not production or no credentials
    if not settings.is_production() and not settings.PROJECT_ID:
         logger.warning("Vision Interface: Running in Mock Mode (No Project ID)")
         return GymEquipmentDescription(
            detected_equipment=["Mock Power Rack", "Mock Dumbbells"],
            confidence_score=0.5
        )

    try:
        # Initialize Vertex AI (Idempotent)
        vertexai.init(project=settings.PROJECT_ID, location=settings.GCP_REGION)
        
        # Use the configured model ID (e.g. gumini-2.0-flash-exp or stable)
        model = GenerativeModel(settings.GEMINI_MODEL_ID) 

        # Create Image Part
        image = Image.from_bytes(image_bytes)
        
        prompt = """
        You are an expert fitness equipment identifier.
        Analyze this image and list the visible gym equipment available for a workout.
        Do not list people or minor objects (water bottles, towels).
        Focus on: Racks, Dumbbells, Machines, Cardio Equipment.
        
        Output stricly valid JSON with this schema:
        {
            "detected_equipment": ["item1", "item2"],
            "confidence_score": 0.95
        }
        """

        response = model.generate_content(
            [image, prompt],
            generation_config={"response_mime_type": "application/json"} 
        )
        
        # Parse JSON
        result = json.loads(response.text)
        logger.info(f"Vision Analysis Success: {result}")
        return GymEquipmentDescription(
            detected_equipment=result.get("detected_equipment", []),
            confidence_score=result.get("confidence_score", 0.0)
        )

    except Exception as e:
        logger.error(f"Gemini Vision Error: {e}")
        # Fallback to avoid breaking flow
        return GymEquipmentDescription(detected_equipment=["Unavailable - Vision Error"], confidence_score=0.0)

def analyze_form(video_bytes: bytes) -> str:
    """
    Analyzes a video clip of an exercise and provides form feedback.
    """
    if not settings.is_production() and not settings.PROJECT_ID:
        return "MOCK: Your squat depth looks good, but keep your chest up. (Dev Mode)"

    try:
        # Initialize Vertex AI
        vertexai.init(project=settings.PROJECT_ID, location=settings.GCP_REGION)
        model = GenerativeModel(settings.GEMINI_MODEL_ID)

        # Create Video Part (Gemini 1.5/2.0 supports inline data for small clips)
        video_part = Part.from_data(data=video_bytes, mime_type="video/mp4")
        
        prompt = """
        You are an elite Strength & Conditioning Coach.
        Analyze this video clip of a client performing an exercise.
        Identify the exercise.
        Critique their form (Technique, Stability, Tempo).
        Provide 1-2 actionable cues to improve.
        Be encouraging but technical.
        """

        response = model.generate_content([video_part, prompt])
        logger.info("Video Analysis Success")
        return response.text

    except Exception as e:
        logger.error(f"Gemini Video Error: {e}")
        return "I couldn't analyze the video properly. Please try again with better lighting or a clearer angle."
