from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
    suggested_plan_override: dict

@router.post("/simulate-morning", response_model=MorningBriefingResponse)
async def simulate_morning_briefing(
    payload: BiometricSimulationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Simulates a 'Morning Briefing' by accepting mock biometric data and generating 
    a proactive intervention using the Concierge Synthesis Engine.
    """
    try:
        # 1. Persist the simulated biometrics for history
        biometrics = DailyBiometrics(
            user_id=current_user.uid,
            sleep_score=payload.sleep_score,
            recovery_status=payload.recovery_status,
            date=datetime.utcnow()
        )
        db.add(biometrics)
        await db.commit()
        await db.refresh(biometrics)

        # 2. Generate the briefing
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

        return MorningBriefingResponse(
            insight_headline=insight.insight_headline,
            actionable_advice=insight.actionable_advice,
            suggested_plan_override=insight.suggested_plan_override
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve briefing: {str(e)}"
        )

