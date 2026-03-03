"""
Sentry API Route — Manual trigger for the Biometric Sentry graph.

Provides a POST endpoint to run the autonomous sentry loop on-demand,
useful for demos, testing, and scheduled cron triggers.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user, AuthenticatedUser
from app.schema import SentryResult
from app.sentry_graph import run_sentry_for_user

router = APIRouter(prefix="/sentry", tags=["Sentry"])


@router.post("/run", response_model=SentryResult)
async def trigger_sentry(
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Trigger the Biometric Sentry loop for the authenticated user.
    
    This runs the full LangGraph pipeline:
    Ingest → Evaluate → [Synthesize → Act] or [Short-circuit].
    
    Returns the complete SentryResult including any session mutations
    and notification payloads.
    """
    try:
        result = await run_sentry_for_user(
            user_id=current_user.uid,
            db=db,
        )
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentry execution failed: {str(e)}",
        )


@router.post("/run/{user_id}", response_model=SentryResult)
async def trigger_sentry_for_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Trigger the Biometric Sentry loop for a specific user (admin/trainer use).
    Useful for cron-job or batch triggers across multiple users.
    """
    # Basic authorization: only trainers/admins can trigger for other users
    if not (current_user.is_trainer or current_user.is_admin):
        if current_user.uid != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only trigger the sentry for your own account.",
            )

    try:
        result = await run_sentry_for_user(
            user_id=user_id,
            db=db,
        )
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentry execution failed: {str(e)}",
        )
