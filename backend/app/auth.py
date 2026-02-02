"""
Firebase Authentication Module for Elite Concierge AI.

Provides:
- Firebase Admin SDK initialization
- Token verification dependency for FastAPI
- Role-based access control
"""
import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

from app.config import settings, logger
from app.database import get_db
from app.models import User

# Initialize Firebase Admin SDK
_firebase_app = None

def get_firebase_app():
    """Lazy initialization of Firebase Admin SDK."""
    global _firebase_app
    if _firebase_app is None:
        try:
            # In production, use GOOGLE_APPLICATION_CREDENTIALS or explicit cred
            if settings.FIREBASE_CREDENTIALS_JSON:
                import json
                cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
                cred = credentials.Certificate(cred_dict)
                _firebase_app = firebase_admin.initialize_app(cred)
            else:
                # Use Application Default Credentials (works in Cloud Run)
                _firebase_app = firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK initialized")
        except Exception as e:
            logger.warning(f"Firebase initialization skipped: {e}")
    return _firebase_app

# Security scheme
bearer_scheme = HTTPBearer(auto_error=False)

class AuthenticatedUser:
    """Represents the authenticated user from Firebase + DB lookup."""
    def __init__(self, uid: str, email: Optional[str], role: str, db_user: Optional[User] = None):
        self.uid = uid
        self.email = email
        self.role = role
        self.db_user = db_user
    
    @property
    def is_trainer(self) -> bool:
        return self.role == "trainer"
    
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
    
    @property
    def is_client(self) -> bool:
        return self.role == "client"


from fastapi import Header

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    api_key: Optional[str] = Header(None, alias="X-Elite-Key"),
    db: AsyncSession = Depends(get_db)
) -> AuthenticatedUser:
    """
    Verify Firebase ID token and return authenticated user.
    Falls back to API key auth for backwards compatibility.
    """
    
    if credentials is None:
        # Check API Key
        primary_key = os.getenv("ELITE_API_KEY")
        
        # Debug logging
        logger.info(f"Auth Check: Bearer=None, KeyProvided={'Yes' if api_key else 'No'}, KeyMatch={api_key == primary_key}")
        
        if api_key == primary_key:
             return AuthenticatedUser(
                uid="demo_user",
                email="admin@example.com",
                role="admin",
                db_user=None
            )
        
        # Also try case-insensitive/alternative? (Just in case)
        
        # No bearer token - check if we're in dev mode with API key
        if settings.ENV == "development":
            # Return demo user for local dev
            return AuthenticatedUser(
                uid="demo_user",
                email="demo@example.com",
                role="admin",
                db_user=None
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    
    # Bypass for E2E Testing using Bearer Token
    primary_key = os.getenv("ELITE_API_KEY")
    
    # Debug logging
    logger.info(f"Auth Check V5: Token len={len(token)}, Key len={len(primary_key)}")
    if token.strip() == primary_key.strip():
         logger.info("Auth: Bearer token matches API Key (V5). Granting Admin access.")
         return AuthenticatedUser(
            uid="demo_user",
            email="admin@example.com",
            role="admin",
            db_user=None
        )

    # Verify Firebase token
    try:
        get_firebase_app()  # Ensure initialized
        decoded_token = firebase_auth.verify_id_token(token)
        uid = decoded_token["uid"]
        email = decoded_token.get("email")
        
        logger.info(f"Authenticated Firebase user: {uid}")
        
    except firebase_admin.exceptions.FirebaseError as e:
        logger.warning(f"Firebase auth failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        # If Firebase not configured, fall back to dev mode
        if settings.ENV == "development":
            logger.warning(f"Firebase not configured, using dev fallback: {e}")
            return AuthenticatedUser(
                uid="demo_user",
                email="demo@example.com", 
                role="admin",
                db_user=None
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication service unavailable"
        )
    
    # Look up user in database
    stmt = select(User).where(User.id == uid)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()
    
    # Auto-create user on first login
    if db_user is None:
        db_user = User(
            id=uid,
            email=email,
            role="client"  # Default to client, trainer promotes later
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"Created new user: {uid}")
    
    return AuthenticatedUser(
        uid=uid,
        email=email,
        role=db_user.role,
        db_user=db_user
    )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[AuthenticatedUser]:
    """Optional auth - returns None if no valid token."""
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_role(*allowed_roles: str):
    """
    Dependency factory that requires specific roles.
    
    Usage:
        @app.get("/admin-only", dependencies=[Depends(require_role("admin"))])
    """
    async def role_checker(user: AuthenticatedUser = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of: {', '.join(allowed_roles)}"
            )
        return user
    return role_checker


# Convenience dependencies
require_trainer = require_role("trainer", "admin")
require_admin = require_role("admin")
