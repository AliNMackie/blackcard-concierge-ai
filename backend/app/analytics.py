from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime
import uuid

from app.database import get_db
from app.models import PerformanceMetric, User
from app.auth import get_current_user, AuthenticatedUser
from app.schema import MetricCreate, MetricResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.post("/metrics", response_model=MetricResponse)
async def log_metric(
    metric_in: MetricCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually log a performance metric.
    """
    new_metric = PerformanceMetric(
        id=str(uuid.uuid4()),
        user_id=current_user.uid,
        category=metric_in.category,
        name=metric_in.name,
        value=metric_in.value,
        unit=metric_in.unit,
        notes=metric_in.notes,
        logged_by=current_user.uid,
        timestamp=metric_in.timestamp or datetime.utcnow()
    )
    
    db.add(new_metric)
    await db.commit()
    await db.refresh(new_metric)
    
    return new_metric

@router.get("/metrics", response_model=List[MetricResponse])
async def get_metrics(
    category: str = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve logged metrics for the current user.
    """
    stmt = select(PerformanceMetric).where(PerformanceMetric.user_id == current_user.uid)
    if category:
        stmt = stmt.where(PerformanceMetric.category == category)
    
    stmt = stmt.order_by(PerformanceMetric.timestamp.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

# --- Aggregators ---

from app.schema import StrengthMetric, EngineMetric, ReadinessMetric

@router.get("/strength", response_model=StrengthMetric)
async def get_strength_analytics(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns aggregated Strength data (e.g. Squat 1RM trend).
    """
    # 1. Fetch 'strength' metrics
    stmt = select(PerformanceMetric).where(
        (PerformanceMetric.user_id == current_user.uid) & 
        (PerformanceMetric.category == 'strength')
    ).order_by(PerformanceMetric.timestamp.asc())
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    # 2. Mock/Calculate Logic (MVP: Just take the latest 'Squat' or similar)
    if not logs:
        return StrengthMetric(estimated_1rm=0, exercise="Squat", trend="stable", history=[])
        
    history = [{"date": m.timestamp.strftime("%Y-%m-%d"), "value": m.value} for m in logs]
    latest = logs[-1].value
    
    # Simple Trend
    trend = "stable"
    if len(logs) >= 2:
        prev = logs[-2].value
        if latest > prev: trend = "up"
        elif latest < prev: trend = "down"
            
    return StrengthMetric(
        estimated_1rm=latest,
        exercise=logs[-1].name or "Compound",
        trend=trend,
        history=history
    )

@router.get("/engine", response_model=EngineMetric)
async def get_engine_analytics(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns Engine capacity (FTP/Run Pace).
    """
    stmt = select(PerformanceMetric).where(
        (PerformanceMetric.user_id == current_user.uid) & 
        (PerformanceMetric.category == 'engine')
    ).order_by(PerformanceMetric.timestamp.asc())
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    if not logs:
        return EngineMetric(ftp=0, vo2_max=None, history=[])
    
    history = [{"date": m.timestamp.strftime("%Y-%m-%d"), "value": m.value} for m in logs]
    latest = logs[-1].value
    
    return EngineMetric(ftp=latest, vo2_max=None, history=history)

@router.get("/readiness", response_model=ReadinessMetric)
async def get_readiness_analytics(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns Readiness/Recovery (HRV/Sleep).
    """
    # For MVP, we might look for daily logs or specific metrics
    # Here we assume 'readiness' category metrics are logged (0-100)
    stmt = select(PerformanceMetric).where(
        (PerformanceMetric.user_id == current_user.uid) & 
        (PerformanceMetric.category == 'readiness')
    ).order_by(PerformanceMetric.timestamp.asc())
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    if not logs:
        return ReadinessMetric(score=85, hrv=0, sleep_score=0, history=[])
        
    history = [{"date": m.timestamp.strftime("%Y-%m-%d"), "value": m.value} for m in logs]
    latest_score = int(logs[-1].value)
    
    return ReadinessMetric(
        score=latest_score,
        hrv=0, # Placeholder if not logging specific HRV
        sleep_score=0,
        history=history
    )
