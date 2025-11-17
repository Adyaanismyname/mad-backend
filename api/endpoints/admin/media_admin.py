"""
Admin endpoints for media management and maintenance.

These endpoints are for administrative tasks like cleanup, monitoring, and debugging.
Should be restricted to admin users only in production.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from core.auth import verify_user_token
from core.media_cleanup import (
    cleanup_expired_pending_uploads,
    get_pending_uploads_stats
)
from schemas.core import StandardResponse
from models.user import User, UserRole
from sqlalchemy import select
from uuid import UUID

router = APIRouter(prefix="/admin/media", tags=["Admin - Media"])


async def verify_admin_user(
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Verify that the current user has admin privileges."""
    user_id = UUID(str(current_user.get("user_id")))
    
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # For now, check if user is a COACH or BOTH (in production, add proper admin role)
    # TODO: Add proper admin role to UserRole enum
    if user.role not in [UserRole.COACH, UserRole.BOTH]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return user


@router.post("/cleanup-pending-uploads", response_model=StandardResponse)
async def trigger_pending_uploads_cleanup(
    cleanup_s3_files: bool = True,
    max_age_hours: int = 24,
    _admin_user: User = Depends(verify_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger cleanup of expired pending uploads.
    
    This endpoint is useful for:
    - Manual maintenance
    - Testing cleanup logic
    - Emergency cleanup after issues
    
    Args:
        cleanup_s3_files: If True, delete orphaned S3 files (default: True)
        max_age_hours: Delete records older than this many hours (default: 24)
    
    Returns:
        Statistics about the cleanup operation
    """
    try:
        stats = await cleanup_expired_pending_uploads(
            db=db,
            cleanup_orphaned_s3=cleanup_s3_files,
            max_age_hours=max_age_hours
        )
        
        return StandardResponse(
            data=stats,
            message=f"Cleanup completed: {stats['expired_marked']} expired, "
                    f"{stats['s3_files_deleted']} S3 files deleted, "
                    f"{stats['records_deleted']} records removed"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/pending-uploads-stats", response_model=StandardResponse)
async def get_pending_uploads_statistics(
    _admin_user: User = Depends(verify_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about pending uploads.
    
    Useful for:
    - Monitoring system health
    - Identifying issues with upload workflow
    - Understanding usage patterns
    
    Returns:
        Statistics including counts by status
    """
    try:
        stats = await get_pending_uploads_stats(db)
        
        return StandardResponse(
            data=stats,
            message="Pending uploads statistics retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )
