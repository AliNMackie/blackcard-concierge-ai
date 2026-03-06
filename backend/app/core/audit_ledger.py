import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AIInterventionLedger
from datetime import datetime

logger = logging.getLogger("elite-concierge")

class AuditLedger:
    @staticmethod
    async def log_intervention(
        db: AsyncSession,
        user_id: str,
        session_id: str,
        biometric_trigger: Dict[str, Any],
        original_protocol: List[Dict[str, Any]],
        mutated_protocol: List[Dict[str, Any]],
        reasoning: str
    ):
        """
        Records an autonomous intervention into the immutable ledger.
        """
        try:
            entry = AIInterventionLedger(
                user_id=user_id,
                session_id=session_id,
                biometric_trigger=biometric_trigger,
                original_protocol=original_protocol,
                mutated_protocol=mutated_protocol,
                reasoning=reasoning
            )
            db.add(entry)
            # We don't commit here; we let the caller handle the transaction
            # but we log for immediate visibility in case of later rollback
            logger.info(f"[AuditLedger] Decision recorded for session {session_id} (User: {user_id})")
        except Exception as e:
            logger.error(f"[AuditLedger] Failed to record intervention: {e}")
            # In a production environment, we might want to raise here 
            # to prevent the intervention from proceeding if auditing fails.
            raise

audit_ledger = AuditLedger()
