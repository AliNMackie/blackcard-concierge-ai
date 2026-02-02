"""
Users Router - Manages user accounts and trainer-client relationships.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models import User
from app.auth import get_current_user, AuthenticatedUser, require_trainer, require_admin
from app.config import logger

router = APIRouter(prefix="/users", tags=["users"])


# --- Schemas ---

class UserResponse(BaseModel):
    id: str
    email: Optional[str]
    role: str
    trainer_id: Optional[str]
    coach_style: str
    is_traveling: bool

    class Config:
        from_attributes = True


class ClientAssignment(BaseModel):
    client_id: str  # User ID or email of client to assign


class UserCreate(BaseModel):
    email: Optional[str] = None
    role: str = "client"
    coach_style: str = "hyrox_competitor"


# --- Endpoints ---

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Get the current authenticated user's profile."""
    if current_user.db_user:
        return current_user.db_user
    
    # Return basic info if no DB user yet
    return UserResponse(
        id=current_user.uid,
        email=current_user.email,
        role=current_user.role,
        trainer_id=None,
        coach_style="hyrox_competitor",
        is_traveling=False
    )


@router.get("/clients", response_model=List[UserResponse])
async def list_trainer_clients(
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_trainer)
):
    """
    List all clients assigned to the current trainer.
    Requires trainer or admin role.
    """
    if current_user.is_admin:
        # Admins see all clients
        stmt = select(User).where(User.role == "client")
    else:
        # Trainers see only their clients
        stmt = select(User).where(User.trainer_id == current_user.uid)
    
    result = await db.execute(stmt)
    clients = result.scalars().all()
    
    logger.info(f"Trainer {current_user.uid} fetched {len(clients)} clients")
    return clients


@router.post("/clients", response_model=UserResponse)
async def assign_client_to_trainer(
    assignment: ClientAssignment,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_trainer)
):
    """
    Assign a client to the current trainer.
    Client can be specified by ID or email.
    """
    # Find client by ID or email
    stmt = select(User).where(
        (User.id == assignment.client_id) | (User.email == assignment.client_id)
    )
    result = await db.execute(stmt)
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client not found: {assignment.client_id}"
        )
    
    if client.role != "client":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only assign users with 'client' role"
        )
    
    if client.trainer_id and client.trainer_id != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client is already assigned to another trainer"
        )
    
    # Assign client to trainer
    client.trainer_id = current_user.uid
    await db.commit()
    await db.refresh(client)
    
    logger.info(f"Assigned client {client.id} to trainer {current_user.uid}")
    return client


@router.delete("/clients/{client_id}")
async def unassign_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_trainer)
):
    """Remove a client from trainer's roster."""
    stmt = select(User).where(User.id == client_id)
    result = await db.execute(stmt)
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check ownership (admin can unassign anyone)
    if not current_user.is_admin and client.trainer_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not your client")
    
    client.trainer_id = None
    await db.commit()
    
    return {"status": "ok", "message": f"Client {client_id} unassigned"}


@router.patch("/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_admin)
):
    """
    Promote/demote a user's role (admin only).
    Valid roles: client, trainer, admin
    """
    if role not in ["client", "trainer", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_role = user.role
    user.role = role
    await db.commit()
    
    logger.info(f"Admin {current_user.uid} changed {user_id} role: {old_role} -> {role}")
    return {"status": "ok", "old_role": old_role, "new_role": role}


async def get_trainer_client_ids(db: AsyncSession, trainer_id: str) -> List[str]:
    """Helper: Get list of client IDs for a trainer."""
    stmt = select(User.id).where(User.trainer_id == trainer_id)
    result = await db.execute(stmt)
    return [row[0] for row in result.fetchall()]
