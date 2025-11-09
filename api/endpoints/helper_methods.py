from fastapi import status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.coach_client_relationship import CoachClientRelationship, RelationshipStatus
from models.user import User, UserRole
from uuid import UUID

# ============= Helper Functions =============

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