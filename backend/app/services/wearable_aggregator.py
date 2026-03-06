import logging
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import DailyBiometrics, User
from datetime import datetime

logger = logging.getLogger("elite-concierge")

class WearableAggregator:
    @staticmethod
    async def ingest_health_data(
        user_id: str, 
        source: str, # "apple_health", "whoop", "garmin"
        raw_data: Dict[str, Any],
        db: AsyncSession
    ) -> DailyBiometrics:
        """
        Normalizes raw payload from wearable APIs and updates DailyBiometrics.
        """
        logger.info(f"Ingesting wearable data from {source} for User {user_id}")
        
        # 1. Normalize based on source
        sleep_score = 0
        recovery_status = "GREEN"
        
        if source == "apple_health":
            # Heuristic calculation for MVP
            sleep_score = raw_data.get("sleep_score", 70)
            avg_hrv = raw_data.get("avg_hrv", 50)
            if avg_hrv < 30: recovery_status = "RED"
            elif avg_hrv < 45: recovery_status = "AMBER"
            
        elif source == "whoop":
            sleep_score = raw_data.get("sleep_performance", 0)
            whoop_recovery = raw_data.get("recovery_score", 0)
            if whoop_recovery < 33: recovery_status = "RED"
            elif whoop_recovery < 66: recovery_status = "AMBER"
            
        # 2. Get or Create DailyBiometrics for today
        today = datetime.utcnow().date()
        stmt = (
            select(DailyBiometrics)
            .where(DailyBiometrics.user_id == user_id)
            .where(DailyBiometrics.date >= datetime.combine(today, datetime.min.time()))
            .limit(1)
        )
        result = await db.execute(stmt)
        bio = result.scalar_one_or_none()
        
        if not bio:
            bio = DailyBiometrics(
                user_id=user_id,
                date=datetime.utcnow(),
                sleep_score=sleep_score,
                recovery_status=recovery_status
            )
            db.add(bio)
        else:
            bio.sleep_score = sleep_score
            bio.recovery_status = recovery_status
            
        await db.commit()
        await db.refresh(bio)
        return bio

wearable_aggregator = WearableAggregator()
