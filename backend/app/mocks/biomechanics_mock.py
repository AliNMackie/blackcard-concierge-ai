import asyncio
from fastapi import APIRouter, File, Form, UploadFile
from typing import Optional

router = APIRouter()

# A static, glowing amber 9:16 SVG to mock the Gemini Vision response.
# Designed to scale perfectly via preserveAspectRatio="xMidYMid slice"
MOCK_SVG = """
<svg width="100%" height="100%" viewBox="0 0 900 1600" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="15" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  
  <g stroke="#fbbf24" fill="none" class="animate-pulse" filter="url(#glow)">
    <!-- Right Leg -->
    <path d="M450,800 L380,1100 L420,1400" stroke-width="8" stroke-dasharray="10 10" />
    <circle cx="450" cy="800" r="15" fill="#f59e0b" /> <!-- Hip -->
    <circle cx="380" cy="1100" r="15" fill="#f59e0b" /> <!-- Knee -->
    <circle cx="420" cy="1400" r="15" fill="#f59e0b" /> <!-- Ankle -->
    
    <!-- Spine / Torso -->
    <path d="M450,400 L450,800" stroke-width="10" stroke-linecap="round"/>
    
    <!-- Shoulders -->
    <line x1="300" y1="400" x2="600" y2="400" stroke-width="12" stroke-linecap="round" />
    <circle cx="300" cy="400" r="12" fill="#f59e0b" /> <!-- Left Shoulder -->
    <circle cx="600" cy="400" r="12" fill="#f59e0b" /> <!-- Right Shoulder -->
  </g>
  
  <text x="50%" y="10%" font-size="28" fill="#fbbf24" font-family="sans-serif" font-weight="900" text-anchor="middle" letter-spacing="4">
    KINETIC DRIFT DETECTED
  </text>
</svg>
"""

@router.post("/api/v1/biomechanics/audit")
async def mock_biomechanics_audit(
    video: UploadFile = File(...),
    movement_type: Optional[str] = Form("unknown")
):
    """
    Mock endpoint for local UI testing.
    Simulates a 2.5s Vertex AI call and returns a static SVG payload.
    """
    # Simulate processing delay
    await asyncio.sleep(2.5)
    
    return {
        "status": "success",
        "movement_type": movement_type,
        "coaching_cue": "Hips are rising slightly faster than the chest. Drive through the mid-foot.",
        "svg_overlay": MOCK_SVG.strip(),
        "drift_score": 0.18
    }
