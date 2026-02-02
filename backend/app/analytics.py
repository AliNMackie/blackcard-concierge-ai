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
