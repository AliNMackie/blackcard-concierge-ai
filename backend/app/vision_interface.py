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
