"""
Background job utilities for media management.

This module provides scheduled tasks for:
- Cleaning up expired pending uploads
- Removing orphaned S3 files
- Maintaining data integrity
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from datetime import datetime, timedelta
from models.pending_upload import PendingUpload
from core.s3_service import get_s3_service
import logging

logger = logging.getLogger(__name__)


async def cleanup_expired_pending_uploads(
    db: AsyncSession,
    cleanup_orphaned_s3: bool = True,
    max_age_hours: int = 24
) -> dict:
    """
    Clean up expired pending uploads from the database.
    
    This function should be run periodically (e.g., every hour) to:
    1. Mark expired pending uploads
    2. Optionally delete orphaned S3 files
    3. Remove old confirmed/failed records
    
    Args:
        db: Database session
        cleanup_orphaned_s3: If True, delete S3 files for expired uploads
        max_age_hours: Delete records older than this (default 24 hours)
    
    Returns:
        dict: Statistics about cleanup operation
    """
    stats = {
        'expired_marked': 0,
        's3_files_deleted': 0,
        'records_deleted': 0,
        'errors': []
    }
    
    try:
        current_time = datetime.utcnow()
        
        # Step 1: Mark expired pending uploads
        result = await db.execute(
            select(PendingUpload).filter(
                and_(
                    PendingUpload.status == 'pending',
                    PendingUpload.expires_at < current_time,
                    PendingUpload.deleted_at.is_(None)
                )
            )
        )
        expired_uploads = result.scalars().all()
        
        for upload in expired_uploads:
            upload.status = 'expired'
            stats['expired_marked'] += 1
            
            # Optionally clean up orphaned S3 files
            if cleanup_orphaned_s3:
                try:
                    s3_service = get_s3_service()
                    if s3_service.delete_file(upload.s3_key):
                        stats['s3_files_deleted'] += 1
                        logger.info(f"Deleted orphaned S3 file: {upload.s3_key}")
                except Exception as e:
                    error_msg = f"Failed to delete S3 file {upload.s3_key}: {str(e)}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
        
        await db.commit()
        
        # Step 2: Delete old records (confirmed, expired, failed)
        cutoff_time = current_time - timedelta(hours=max_age_hours)
        
        delete_stmt = delete(PendingUpload).where(
            and_(
                PendingUpload.status.in_(['confirmed', 'expired', 'failed']),
                PendingUpload.created_at < cutoff_time
            )
        )
        
        result = await db.execute(delete_stmt)
        stats['records_deleted'] = result.rowcount
        await db.commit()
        
        logger.info(
            f"Cleanup completed: {stats['expired_marked']} marked expired, "
            f"{stats['s3_files_deleted']} S3 files deleted, "
            f"{stats['records_deleted']} records deleted"
        )
        
    except Exception as e:
        await db.rollback()
        error_msg = f"Error during cleanup: {str(e)}"
        logger.error(error_msg)
        stats['errors'].append(error_msg)
    
    return stats


async def cleanup_pending_upload_by_id(
    db: AsyncSession,
    upload_id,
    delete_s3_file: bool = True
) -> bool:
    """
    Clean up a specific pending upload.
    
    Useful for manual cleanup or when a specific upload needs to be cancelled.
    
    Args:
        db: Database session
        upload_id: UUID of the pending upload
        delete_s3_file: If True, delete the S3 file as well
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        result = await db.execute(
            select(PendingUpload).filter(PendingUpload.id == upload_id)
        )
        pending_upload = result.scalar_one_or_none()
        
        if not pending_upload:
            return False
        
        # Delete S3 file if requested
        if delete_s3_file and pending_upload.s3_key:
            try:
                s3_service = get_s3_service()
                s3_service.delete_file(pending_upload.s3_key)
            except Exception as e:
                logger.error(f"Failed to delete S3 file {pending_upload.s3_key}: {e}")
        
        # Delete from database
        await db.delete(pending_upload)
        await db.commit()
        
        logger.info(f"Cleaned up pending upload: {upload_id}")
        return True
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error cleaning up pending upload {upload_id}: {e}")
        return False


async def get_pending_uploads_stats(db: AsyncSession) -> dict:
    """
    Get statistics about pending uploads.
    
    Useful for monitoring and dashboards.
    
    Returns:
        dict: Statistics including counts by status
    """
    try:
        # Count by status
        result = await db.execute(select(PendingUpload))
        all_uploads = result.scalars().all()
        
        stats = {
            'total': len(all_uploads),
            'pending': 0,
            'confirmed': 0,
            'expired': 0,
            'failed': 0,
            'pending_expired_but_not_marked': 0
        }
        
        current_time = datetime.utcnow()
        
        for upload in all_uploads:
            stats[upload.status] = stats.get(upload.status, 0) + 1
            
            # Check for expired but not marked
            if upload.status == 'pending' and upload.expires_at < current_time:
                stats['pending_expired_but_not_marked'] += 1
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting pending uploads stats: {e}")
        return {'error': str(e)}


# Example usage with APScheduler or similar:
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db.session import get_db

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', hours=1)
async def scheduled_cleanup():
    async for db in get_db():
        await cleanup_expired_pending_uploads(db, cleanup_orphaned_s3=True)

scheduler.start()
"""
