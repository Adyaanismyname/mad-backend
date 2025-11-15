from fastapi import status, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.coach_client_relationship import CoachClientRelationship, RelationshipStatus
from models.user import User, UserRole
from uuid import UUID
from datetime import datetime, timezone
from core.mailer import send_verification_email
import random

# ============= Helper Functions =============

async def generate_and_send_otp(
    user: User, 
    db: AsyncSession, 
    background_tasks: BackgroundTasks,
    otp_validity_minutes: int = 10
) -> str:
    """
    Generate OTP, save to user, and send email.
    
    Args:
        user: User model instance
        db: Database session
        background_tasks: FastAPI background tasks
        otp_validity_minutes: OTP validity duration in minutes
    
    Returns:
        str: The generated OTP
    """
    # Generate 6-digit OTP
    otp = f"{random.randint(0, 999999):06d}"
    
    # Update user with OTP
    user.otp = otp
    user.otp_created_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(user)
    
    # Send email in background
    background_tasks.add_task(send_verification_email, user.email, otp, otp_validity_minutes)
    
    return otp


async def verify_coach_role(user_id: UUID, db: AsyncSession):
    """Verify that user has coach role."""
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user.role not in [UserRole.COACH, UserRole.BOTH]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only coaches can perform this action"
        )
    return user


async def verify_coach_client_relationship(coach_id: UUID, client_id: UUID, db: AsyncSession):
    """Verify active coach-client relationship."""
    result = await db.execute(
        select(CoachClientRelationship).filter(
            CoachClientRelationship.coach_user_id == coach_id,
            CoachClientRelationship.client_user_id == client_id,
            CoachClientRelationship.status == RelationshipStatus.ACTIVE
        )
    )
    relationship = result.scalar_one_or_none()
    
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active coach-client relationship found"
        )
    return relationship