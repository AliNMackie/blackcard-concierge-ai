"""
Users Router - Manages user accounts and trainer-client relationships.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models import User
from app.auth import get_current_user, AuthenticatedUser, require_trainer, require_admin
from app.config import logger
from app.schema import UserUpdate

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


# --- Trainer Messaging ---

class TrainerMessage(BaseModel):
    message: str
    send_whatsapp: bool = False  # Optionally send via WhatsApp


@router.post("/clients/{client_id}/message")
async def send_message_to_client(
    client_id: str,
    msg: TrainerMessage,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_trainer)
):
    """
    Send a message from trainer to client.
    Message is logged to event_logs and optionally sent via WhatsApp.
    """
    from app.models import EventLog
    
    # Verify client exists and belongs to this trainer
    stmt = select(User).where(User.id == client_id)
    result = await db.execute(stmt)
    client = result.scalar_one_or_none()
    
    if not client:
        if client_id == "1":
            client = User(id="1", role="client")
            db.add(client)
            await db.commit()
            await db.refresh(client)
        else:
            raise HTTPException(status_code=404, detail="Client not found")
    
    # Check ownership (admin can message anyone)
    if not current_user.is_admin and client.trainer_id and client.trainer_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not your client")
    
    # Log message as event
    log_entry = EventLog(
        user_id=client_id,
        event_type="trainer_message",
        payload={
            "from_trainer": current_user.uid,
            "trainer_email": current_user.email,
            "message": msg.message
        },
        agent_decision="TRAINER_DIRECT",
        agent_message=msg.message
    )
    db.add(log_entry)
    await db.commit()
    
    # Optionally send via WhatsApp
    whatsapp_sid = None
    if msg.send_whatsapp and client.id.startswith("whatsapp:"):
        try:
            from app.messaging import send_whatsapp
            whatsapp_sid = send_whatsapp(to=client.id, body=msg.message)
            logger.info(f"Trainer message sent via WhatsApp: {whatsapp_sid}")
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
    
    logger.info(f"Trainer {current_user.uid} messaged client {client_id}")
    
    return {
        "status": "ok",
        "message_id": log_entry.id if hasattr(log_entry, 'id') else None,
        "whatsapp_sid": whatsapp_sid
    }


@router.get("/clients/{client_id}/messages")
async def get_client_messages(
    client_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_trainer)
):
    """
    Get recent messages for a client (both trainer messages and client chats).
    """
    from app.models import EventLog
    
    # Verify access
    stmt = select(User).where(User.id == client_id)
    result = await db.execute(stmt)
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if not current_user.is_admin and client.trainer_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not your client")
    
    # Get chat and trainer_message events
    stmt = select(EventLog).where(
        (EventLog.user_id == client_id) & 
        (EventLog.event_type.in_(["chat", "trainer_message"]))
    ).order_by(EventLog.created_at.desc()).limit(limit)
    
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    return messages


@router.get("/me/travel-status")
async def get_travel_status(db: AsyncSession = Depends(get_db)):
    """
    Reads the travel status for User 1 (Demo Client).
    """
    stmt = select(User).where(User.id == "1")
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        # Auto-create User 1 if missing for MVP/Demo
        user = User(id="1", role="client")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    return {"is_traveling": user.is_traveling}


@router.post("/me/toggle-travel")
async def toggle_travel(db: AsyncSession = Depends(get_db)):
    """
    Toggles the travel mode for User 1 (Demo Client).
    """
    stmt = select(User).where(User.id == "1")
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(id="1", role="client", is_traveling=True)
        db.add(user)
        await db.commit()
    else:
        user.is_traveling = not user.is_traveling
        await db.commit()
        
    return {"is_traveling": user.is_traveling}


@router.patch("/me")
async def update_user_profile(update_data: UserUpdate, db: AsyncSession = Depends(get_db)):
    """
    Updates the Demo Client (User 1) profile settings, including Persona.
    """
    stmt = select(User).where(User.id == "1")
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(id="1", role="client")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    if update_data.is_traveling is not None:
        user.is_traveling = update_data.is_traveling
        
    if update_data.coach_style is not None:
        user.coach_style = update_data.coach_style
        
    await db.commit()
    await db.refresh(user)
    
    return {
        "status": "updated",
        "coach_style": user.coach_style, 
        "is_traveling": user.is_traveling
    }



@router.post("/admin/provision-trainer")
async def provision_trainer(
    email: str = Body(..., embed=True),
    uid: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_admin)
):
    """
    Admin: Provision or upgrade a user to Trainer role by Email.
    Optionally accepts a uid if known (from Firebase Console).
    """
    # 1. Check if user exists by Email
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        # User not in our DB yet — try Firebase lookup or use provided UID
        resolved_uid = uid  # Use provided UID if available
        
        if not resolved_uid:
            try:
                from firebase_admin import auth as fb_auth
                from app.auth import get_firebase_app
                get_firebase_app()
                fb_user = fb_auth.get_user_by_email(email)
                resolved_uid = fb_user.uid
            except Exception as e:
                logger.warning(f"Firebase lookup failed for {email}: {e}")
        
        if not resolved_uid:
            raise HTTPException(
                status_code=404, 
                detail=f"User {email} not found. Provide their Firebase UID or have them sign up first."
            )
        
        # Create DB record with their real UID
        user = User(id=resolved_uid, email=email, role="trainer")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"Admin {current_user.uid} created + promoted {email} (UID: {resolved_uid}) to TRAINER")
        return {"status": "ok", "message": f"User {email} created and promoted to TRAINER"}
        
    user.role = "trainer"
    await db.commit()
    
    logger.info(f"Admin {current_user.uid} promoted {email} to TRAINER")
    return {"status": "ok", "message": f"User {email} is now a TRAINER"}

async def get_trainer_client_ids(db: AsyncSession, trainer_id: str) -> List[str]:
    """Helper: Get list of client IDs for a trainer."""
    stmt = select(User.id).where(User.trainer_id == trainer_id)
    result = await db.execute(stmt)
    return [row[0] for row in result.fetchall()]

