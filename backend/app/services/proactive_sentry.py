import numpy as np
from typing import List, Dict, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.contextual_memory import BiomechanicalSignature
from app.config import logger

async def calculate_roi_score(user_id: str, movement_type: str, db: AsyncSession) -> Dict[str, any]:
    """
    Calculates the 'Risk of Injury' (ROI) score by comparing the last 10 
    biomechanical snapshots against the user's 'Golden Form' baseline.
    
    Formula: ROI = Σ (w_i * distance_i) / Σ w_i
    Where w_i is a time-decay weight: e^-(λ * t)
    """
    try:
        # 1. Fetch Golden Form baseline
        stmt_golden = (
            select(BiomechanicalSignature)
            .where(BiomechanicalSignature.user_id == user_id)
            .where(BiomechanicalSignature.movement_type == movement_type)
            .where(BiomechanicalSignature.is_golden == True)
        )
        result_golden = await db.execute(stmt_golden)
        golden_form = result_golden.scalar_one_or_none()
        
        if not golden_form:
            return {"roi_score": 0.0, "status": "NO_BASELINE", "flagged_deviations": []}

        # 2. Fetch last 10 sessions (excluding golden form if it was a session)
        stmt_history = (
            select(BiomechanicalSignature)
            .where(BiomechanicalSignature.user_id == user_id)
            .where(BiomechanicalSignature.movement_type == movement_type)
            .where(BiomechanicalSignature.is_golden == False)
            .order_by(desc(BiomechanicalSignature.created_at))
            .limit(10)
        )
        result_history = await db.execute(stmt_history)
        history = result_history.scalars().all()
        
        if not history:
            return {"roi_score": 0.0, "status": "INSUFFICIENT_DATA", "flagged_deviations": []}

        # 3. Calculate Weighted Drift
        # Weights: Recent sessions have higher impact (e^-(0.1 * index))
        distances = []
        weights = []
        
        golden_vec = np.array(golden_form.embedding)
        
        for i, entry in enumerate(history):
            entry_vec = np.array(entry.embedding)
            
            # Cosine Distance = 1 - (A.B / (||A||*||B||))
            # Since vectors are normalized during extraction, distance = 1 - dot product
            cos_sim = np.dot(golden_vec, entry_vec)
            distance = 1.0 - cos_sim
            
            weight = np.exp(-0.2 * i) # λ = 0.2 decay
            distances.append(distance)
            weights.append(weight)
        
        weighted_avg_drift = np.average(distances, weights=weights)
        
        # Scale ROI score: 0 (Perfect) to 100 (Critical Failure)
        # Assuming 0.15 drift is 'High Risk'
        roi_score = min(100.0, (weighted_avg_drift / 0.15) * 100.0)
        
        # 4. Identify specific flagged 'joint' deviations
        # (Heuristic: identify which indices in the 768d vector diverged most)
        # In a real system, we'd map indices to joints like 'lumbar_flexion'
        diff = np.abs(golden_vec - np.array(history[0].embedding))
        top_indices = np.argsort(diff)[-3:][::-1] # Top 3 divergencies
        
        deviations = []
        # Mock mapping for MVP visualization
        joint_map = {0: "Lumbar Flexion", 10: "Knee Valgus", 25: "External Rotation Debt"}
        for idx in top_indices:
            label = joint_map.get(int(idx % 30), f"Kinematic Chain Seg #{idx}")
            deviations.append(label)

        return {
            "roi_score": round(roi_score, 2),
            "status": "RED" if roi_score > 70 else ("AMBER" if roi_score > 40 else "GREEN"),
            "drift_magnitude": round(float(weighted_avg_drift), 4),
            "flagged_deviations": deviations
        }

    except Exception as e:
        logger.error(f"ROI Calculation Error: {e}")
        return {"roi_score": 0.0, "status": "ERROR", "flagged_deviations": []}
