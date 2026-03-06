import numpy as np
from typing import List, Dict, Any

class VectorStandardizer:
    """
    Standardizes biomechanical joint landmarks (angles, velocities) into a 
    fixed-length 768-dimensional vector suitable for pgvector storage.
    """
    
    TARGET_DIM = 768

    @classmethod
    def normalize_landmarks(cls, joint_data: Dict[str, Any]) -> List[float]:
        """
        Processes raw joint data (e.g., from Mediapipe/Vision API) and returns 
        a normalized fixed-length vector.
        
        Args:
            joint_data: Dict containing 'angles' (list of floats) and 'velocities' (list of floats).
            
        Returns:
            List[float]: A unit-normalized vector of length 768.
        """
        angles = np.array(joint_data.get("angles", []), dtype=np.float32)
        velocities = np.array(joint_data.get("velocities", []), dtype=np.float32)
        
        # Concatenate features
        raw_vector = np.concatenate([angles, velocities])
        
        # Pad or truncate to TARGET_DIM
        if len(raw_vector) < cls.TARGET_DIM:
            standardized_vector = np.pad(raw_vector, (0, cls.TARGET_DIM - len(raw_vector)), mode='constant')
        else:
            standardized_vector = raw_vector[:cls.TARGET_DIM]
            
        # Unit normalization for Cosine Similarity scaling
        norm = np.linalg.norm(standardized_vector)
        if norm > 0:
            standardized_vector = standardized_vector / norm
            
        return standardized_vector.tolist()
