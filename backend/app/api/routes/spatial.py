"""
Spatial API Route — Exposes the Spatial Sentry functions.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.auth import get_current_user, AuthenticatedUser
from app.services.spatial_sentry import check_spatial_boundary, TravelModeHook

router = APIRouter(prefix="/spatial", tags=["Spatial"])

class LocationPayload(BaseModel):
    latitude: float = Field(..., description="User's current latitude")
    longitude: float = Field(..., description="User's current longitude")


@router.post("/check-location", response_model=TravelModeHook)
async def check_location(
    payload: LocationPayload,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Client sends GPS coordinates to check against their Home Base.
    If they are > 50km away, this triggers Ghost Mode and returns the Hook payload.
    """
    try:
        hook_result = await check_spatial_boundary(
            user_id=current_user.uid,
            current_lat=payload.latitude,
            current_lon=payload.longitude,
            db=db,
        )
        return hook_result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Location check failed: {str(e)}",
        )
