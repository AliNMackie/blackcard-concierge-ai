"""
Biomechanical Audit Endpoint — Level 5 Multimodal Analysis

Accepts a sequence of video frames (base64 encoded), retrieves the user's
"Golden Form" BiomechanicalSignature from pgvector, and uses Gemini 3.1 Pro 
to analyze the movement and output a dynamic SVG of joint paths and fatigue.
"""
import logging
import json
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from google.cloud import storage

from app.database import get_db
from app.auth import get_current_user, AuthenticatedUser
from app.config import settings
from app.core.pubsub import publisher

logger = logging.getLogger("elite-concierge")

router = APIRouter(prefix="/biomechanics", tags=["Biomechanics"])

class BiomechanicalAuditRequest(BaseModel):
    movement_type: str = Field(
        description="Type of movement, e.g., 'barbell_squat', 'deadlift'"
    )
    video_base64: Optional[str] = Field(
        default=None,
        description="Base64 encoded video file (mp4 preferred). Optional for Elite tier."
    )
    vectors: Optional[List[float]] = Field(
        default=None,
        description="Pre-extracted 768d biomechanical vectors. Required if video_base64 is missing."
    )

class BiomechanicalAuditResponse(BaseModel):
    job_id: str
    status: str = "accepted"
    message: str

async def upload_to_gcs(bucket_name: str, blob_name: str, data_b64: str):
    """Encapsulates the storage upload logic."""
    import base64
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    video_data = base64.b64decode(data_b64)
    blob.upload_from_string(video_data, content_type="video/mp4")
    return f"gs://{bucket_name}/{blob_name}"

@router.post("/audit", response_model=BiomechanicalAuditResponse, status_code=status.HTTP_202_ACCEPTED)
async def audit_biomechanics(
    payload: BiomechanicalAuditRequest,
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Asynchronous Biomechanical Audit:
    1. If vectors are provided (Elite tier), publish directly to Pub/Sub.
    2. Otherwise, upload video to GCS and queue for server-side extraction.
    """
    job_id = str(uuid.uuid4())
    logger.info(f"[Biomechanics] Initiating async audit {job_id} for user {current_user.uid}")

    # Case A: Edge-extracted vectors provided (Elite Tier)
    if payload.vectors:
        logger.info(f"[Biomechanics] Edge vectors received for audit {job_id}")
        # Publish vector data directly. The worker will recognize this is a vector-only job.
        publisher.publish_vector_job(
            job_id=job_id,
            user_id=current_user.uid,
            movement_type=payload.movement_type,
            vector=payload.vectors
        )
        return BiomechanicalAuditResponse(
            job_id=job_id,
            status="accepted",
            message="Edge vectors received and queued for analysis."
        )

    # Case B: Traditional Video Upload
    if not payload.video_base64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either video_base64 or vectors must be provided."
        )

    bucket_name = settings.GCS_BUCKET_NAME if hasattr(settings, "GCS_BUCKET_NAME") else f"{settings.PROJECT_ID}-biomechanics"
    blob_name = f"uploads/{current_user.uid}/{job_id}.mp4"
    
    try:
        video_uri = await upload_to_gcs(bucket_name, blob_name, payload.video_base64)
        publisher.publish_video_job(video_uri, current_user.uid, payload.movement_type)
        
        return BiomechanicalAuditResponse(
            job_id=job_id,
            status="accepted",
            message="Video uploaded and queued for processing."
        )
        
    except Exception as e:
        logger.error(f"[Biomechanics] Failed to queue audit {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue processing: {str(e)}"
        )
