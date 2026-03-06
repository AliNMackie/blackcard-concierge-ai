from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database import get_db
from app.auth import get_current_user, AuthenticatedUser
from app.services.wearable_aggregator import wearable_aggregator

router = APIRouter(prefix="/wearables", tags=["Wearables"])

@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_wearable_data(
    payload: Dict[str, Any],
    source: str = "apple_health",
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Endpoint for syncing wearable health data (Sleep, HRV, Recovery).
    """
    try:
        biometrics = await wearable_aggregator.ingest_health_data(
            user_id=current_user.uid,
            source=source,
            raw_data=payload,
            db=db
        )
        return {
            "status": "success",
            "message": f"Biometrics updated for {biometrics.date.date()}",
            "recovery_status": biometrics.recovery_status
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest data: {str(e)}"
        )
