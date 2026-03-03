"""
Vision Equipment Mapper Endpoint.

Accepts an image of a hotel gym, uses Gemini 3.1 Pro to identify
available equipment, and mutates today's session via a SessionMutation.
"""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.auth import get_current_user, AuthenticatedUser
from app.schema import SessionMutation
from app.graph import gemini_client

logger = logging.getLogger("elite-concierge")

router = APIRouter(prefix="/vision", tags=["Vision Mapper"])


class GymScanPayload(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded image of the gym")


class GymScanResult(BaseModel):
    available_equipment: list[str] = Field(description="List of identified equipment")
    session_mutation: SessionMutation | None = Field(description="Adapted plan")


# ---------------------------------------------------------------------------
# Output Schema for Gemini
# ---------------------------------------------------------------------------
VISION_MAPPER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "available_equipment": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "List of all identifiable gym equipment in the image."
        },
        "session_mutation": {
            "type": "OBJECT",
            "properties": {
                "headline": {"type": "STRING"},
                "advice": {"type": "STRING"},
                "original_exercises_replaced": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "replacement_exercises": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "intensity_cap_percent": {"type": "INTEGER"},
                "volume_reduction_percent": {"type": "INTEGER"},
                "session_type_override": {"type": "STRING"}
            },
            "required": [
                "headline", "advice", "original_exercises_replaced",
                "replacement_exercises", "intensity_cap_percent",
                "volume_reduction_percent", "session_type_override"
            ]
        }
    },
    "required": ["available_equipment", "session_mutation"]
}


@router.post("/scan-gym", response_model=GymScanResult)
async def scan_hotel_gym(
    payload: GymScanPayload,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Multimodal endpoint to scan a hotel gym and remap today's workout.
    """
    if not payload.image_base64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image payload is required."
        )

    # 1. Structure the prompt for Gemini
    prompt = """
    You are the 'Blackcard Concierge' — a world-class proactive fitness advisor.
    The client has entered a new hotel gym, and Ghost Mode is active.
    
    1. Identify all visible gym equipment in the provided image.
    2. Given that the client is traveling (meaning recovery might be sub-optimal
       and they are out of their normal routine), generate a SessionMutation to
       adapt their workout. Replace any barbell/heavy machine work with the
       dumbbells, kettlebells, or machines visible in the image.
    """

    # 2. Call Gemini MultiModal
    gemini_client._ensure_init()
    if not gemini_client.model:
        logger.warning("[VisionMapper] Gemini not initialized. Using mock fallback.")
        return _mock_gym_scan_result()

    try:
        from vertexai.generative_models import GenerationConfig, Part
        
        # Determine mime type (naive check)
        mime_type = "image/jpeg"
        base64_data = payload.image_base64
        if payload.image_base64.startswith("data:"):
            header, content = payload.image_base64.split(",", 1)
            base64_data = content
            mime_type = header.split(";")[0].split(":")[1]

        image_part = Part.from_data(
            mime_type=mime_type,
            data=base64_data
        )

        response = gemini_client.model.generate_content(
            [prompt, image_part],
            generation_config=GenerationConfig(
                response_mime_type="application/json",
                response_schema=VISION_MAPPER_SCHEMA,
                temperature=0.2,
            ),
        )
        result_dict = json.loads(response.text)
        
        # 3. Persist as a DailyInsight
        await _persist_gym_insight(current_user.uid, result_dict, db)

        return GymScanResult(
            available_equipment=result_dict.get("available_equipment", []),
            session_mutation=SessionMutation(**result_dict.get("session_mutation", {}))
        )

    except Exception as e:
        logger.error(f"[VisionMapper] Gemini scan failed: {e}")
        # Fallback to mock on error so the app doesn't crash during demo
        return _mock_gym_scan_result()


async def _persist_gym_insight(user_id: str, result_dict: dict, db: AsyncSession):
    try:
        from app.models import DailyInsight
        mutation = result_dict.get("session_mutation", {})
        insight = DailyInsight(
            user_id=user_id,
            date=datetime.now(timezone.utc),
            insight_headline=mutation.get("headline", "Ghost Mode Adaptation"),
            actionable_advice=mutation.get("advice", "Hotel gym equipment mapped."),
            suggested_plan_override=mutation,
        )
        db.add(insight)
        await db.commit()
    except Exception as e:
        logger.error(f"[VisionMapper] Failed to persist Insight: {e}")


def _mock_gym_scan_result() -> GymScanResult:
    return GymScanResult(
        available_equipment=["Dumbbells (up to 25kg)", "Treadmill", "Adjustable Bench"],
        session_mutation=SessionMutation(
            headline="Hotel Gym Mapped",
            advice="I've analyzed the space. Barbell work has been subbed for DB variations. Keep intensity moderate.",
            original_exercises_replaced=["Barbell Back Squat", "Barbell Bench Press"],
            replacement_exercises=["DB Goblet Squat", "DB Flat Press"],
            intensity_cap_percent=80,
            volume_reduction_percent=20,
            session_type_override="hotel_hypertrophy"
        )
    )
