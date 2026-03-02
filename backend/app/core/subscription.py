from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.auth import get_current_user, AuthenticatedUser

FREE_TIER_LIMIT = 3

async def verify_premium_tier(
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> User:
    """
    Checks if the user has reached their AI Coach adaptation limit.
    Free users get a maximum of 3 adaptations. Premium/Elite users are unlimited.
    Returns the User model so the endpoint can update the usage count.
    """
    stmt = select(User).where(User.id == current_user.uid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        # Create minimal user if they don't exist yet but passed auth
        user = User(id=current_user.uid, role="client", tier="free", ai_usage_count=0)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    if user.tier == "free" and user.ai_usage_count >= FREE_TIER_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "paywall_required",
                "message": "You've reached your free limit of AI Coach adaptations. Please upgrade to Premium.",
                "limit": FREE_TIER_LIMIT
            }
        )
        
    return user
