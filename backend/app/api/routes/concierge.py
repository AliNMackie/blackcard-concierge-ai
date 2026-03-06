from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any

from datetime import datetime

from app.database import get_db
from app.models import User, DailyBiometrics, DailyInsight
from app.auth import get_current_user, AuthenticatedUser
from app.services.concierge import generate_morning_briefing

router = APIRouter(prefix="/concierge", tags=["Concierge"])

class BiometricSimulationRequest(BaseModel):
    sleep_score: int
    recovery_status: str # RED, AMBER, GREEN

class MorningBriefingResponse(BaseModel):
    insight_headline: str
    actionable_advice: str
    risk_of_injury_score: float
    mechanical_flags: List[str]
    suggested_plan_override: Optional[Dict[str, Any]]

@router.post("/simulate-morning", response_model=MorningBriefingResponse)
async def simulate_morning_briefing(
    payload: BiometricSimulationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Simulates a 'Morning Briefing' by accepting mock biometric data and generating 
    a proactive intervention using the Concierge Synthesis Engine + Predictive Sentry.
    """
    try:
        # 1. Persist the simulated biometrics
        biometrics = DailyBiometrics(
            user_id=current_user.uid,
            sleep_score=payload.sleep_score,
            recovery_status=payload.recovery_status,
            date=datetime.utcnow()
        )
        db.add(biometrics)
        await db.commit()
        await db.refresh(biometrics)

        # 2. Generate the briefing (Internal ROI calculation happens here)
        briefing = await generate_morning_briefing(
            user_id=current_user.uid,
            biometrics=biometrics,
            db=db
        )

        # 3. Persist the insight
        insight = DailyInsight(
            user_id=current_user.uid,
            date=datetime.utcnow(),
            insight_headline=briefing.get("insight_headline", "Daily Briefing"),
            actionable_advice=briefing.get("actionable_advice", ""),
            suggested_plan_override=briefing.get("suggested_plan_override") or {}
        )
        db.add(insight)
        await db.commit()

        return MorningBriefingResponse(
            insight_headline=insight.insight_headline,
            actionable_advice=insight.actionable_advice,
            risk_of_injury_score=briefing.get("risk_of_injury_score", 0.0),
            mechanical_flags=briefing.get("mechanical_flags", []),
            suggested_plan_override=insight.suggested_plan_override
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Concierge simulation failed: {str(e)}"
        )

@router.get("/today", response_model=MorningBriefingResponse)
async def get_today_briefing(
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Retrieves the latest 'Morning Briefing' generated for the current user.
    """
    try:
        # Note: In a real app, we'd store the ROI and Flags in the DailyInsight table.
        # For this MVP iteration, we recalculate or fetch the latest.
        stmt = (
            select(DailyInsight)
            .where(DailyInsight.user_id == current_user.uid)
            .order_by(DailyInsight.date.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        insight = result.scalar_one_or_none()

        if not insight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No briefing generated for today yet."
            )

        # Mock/Recalculate metadata for the response
        return MorningBriefingResponse(
            insight_headline=insight.insight_headline,
            actionable_advice=insight.actionable_advice,
            risk_of_injury_score=0.0, # Placeholder
            mechanical_flags=[],      # Placeholder
            suggested_plan_override=insight.suggested_plan_override
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve briefing: {str(e)}"
        )
