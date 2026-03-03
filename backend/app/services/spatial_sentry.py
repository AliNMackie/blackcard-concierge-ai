"""
Spatial Sentry — Autonomous Location Awareness

Implements the Haversine formula to calculate the great-circle distance
between two points on a sphere given their longitudes and latitudes.
Detects when the user is more than 50km away from their "Home Base"
and toggles the `is_traveling` state for Ghost Mode.
"""
import math
import logging
from typing import Optional
from typing_extensions import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User

logger = logging.getLogger("elite-concierge")

# ---------------------------------------------------------------------------
# Configuration & Constants
# ---------------------------------------------------------------------------
EARTH_RADIUS_KM = 6371.0
GHOST_MODE_THRESHOLD_KM = 50.0

# Strathaven, Scotland (Home Base)
HOME_BASE_LAT = 55.6797
HOME_BASE_LON = -4.0664


# ---------------------------------------------------------------------------
# Mathematical Core
# ---------------------------------------------------------------------------
def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth's surface.
    
    Uses the exact formula:
    d = 2r \arcsin(\sqrt{\sin^2(\frac{\phi_2 - \phi_1}{2}) + \cos(\phi_1)\cos(\phi_2)\sin^2(\frac{\lambda_2 - \lambda_1}{2})})
    """
    # Convert latitude and longitude from degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    lambda1 = math.radians(lon1)
    lambda2 = math.radians(lon2)

    # Differences in coordinates
    delta_phi = phi2 - phi1
    delta_lambda = lambda2 - lambda1

    # Haversine formula core
    a_term = math.sin(delta_phi / 2.0)**2
    b_term = math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    
    # 2r * arcsin(sqrt(a + b)) -> 2r * atan2(sqrt(a), sqrt(1-a)) is equivalent but safer
    # The prompt explicitly asked for the arcsin(sqrt(...)) form:
    internal_sqrt = math.sqrt(a_term + b_term)
    
    # Protect against float precision issues pushing > 1.0 before arcsin
    if internal_sqrt > 1.0:
        internal_sqrt = 1.0
        
    distance_km = 2.0 * EARTH_RADIUS_KM * math.asin(internal_sqrt)
    
    return distance_km


# ---------------------------------------------------------------------------
# State Management
# ---------------------------------------------------------------------------
class TravelModeHook(TypedDict):
    distance_km: float
    is_traveling: bool
    status_changed: bool
    message: str


async def check_spatial_boundary(user_id: str, current_lat: float, current_lon: float, db: AsyncSession) -> TravelModeHook:
    """
    Evaluates the user's current coordinates against Home Base.
    If distance > 50km, toggles `is_traveling=True` and returns a hook payload
    to trigger the Next.js Ghost Mode.
    Returns to False if within 50km.
    """
    distance = calculate_haversine_distance(HOME_BASE_LAT, HOME_BASE_LON, current_lat, current_lon)
    distance = round(distance, 2)
    
    is_now_traveling = distance > GHOST_MODE_THRESHOLD_KM
    
    status_changed = False
    message = f"Location checked: {distance}km from base."
    
    if db:
        try:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                # If the state is changing, update the DB
                if user.is_traveling != is_now_traveling:
                    user.is_traveling = is_now_traveling
                    if is_now_traveling:
                        user.equipment_constraint = "Unknown Hotel Gym" # Forces vision scan
                        message = f"Ghost Mode Activated. You are {distance}km from home."
                        logger.info(f"[SpatialSentry] {user_id} departed home radius ({distance}km). Ghost Mode ON.")
                    else:
                        user.equipment_constraint = "Full Gym"
                        message = f"Welcome back. Resuming standard protocols."
                        logger.info(f"[SpatialSentry] {user_id} returned to home radius ({distance}km). Ghost Mode OFF.")
                    
                    await db.commit()
                    status_changed = True
                
        except Exception as e:
            logger.error(f"[SpatialSentry] Database update failed: {e}")
            
    return {
        "distance_km": distance,
        "is_traveling": is_now_traveling,
        "status_changed": status_changed,
        "message": message
    }
