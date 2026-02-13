"""
Automatic background worker for pose detection that runs with the FastAPI app.
"""

import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select

from db.session import SessionLocal
from models.media_upload import MediaUpload
from core.s3_service import get_s3_service
from core.pose_detection_service import get_pose_detection_service

logger = logging.getLogger(__name__)


class PoseDetectionWorker:
    """Background worker that processes pending pose detection tasks."""
    
    def __init__(self, interval: int = 10, batch_size: int = 3):
        self.interval = interval
        self.batch_size = batch_size
        self.running = False
        self.task = None
    
    async def process_pending_videos(self):
        """Process videos with pending pose analysis status.
        
        IMPORTANT: DB session is only held during queries/updates, NOT during
        CPU-heavy pose detection. This prevents blocking API requests.
        """
        try:
            # Step 1: Fetch pending videos and mark as processing (quick DB op)
            pending_jobs = []
            async with SessionLocal() as db:
                result = await db.execute(
                    select(MediaUpload)
                    .filter(
                        MediaUpload.media_type == "video",
                        MediaUpload.pose_analysis_status == "pending",
                        MediaUpload.s3_key.isnot(None)
                    )
                    .limit(self.batch_size)
                )
                pending_videos = result.scalars().all()
                
                if not pending_videos:
                    # Log at debug level to avoid spam, but helps with troubleshooting
                    logger.debug("[WORKER] No pending videos found")
                    return
                
                logger.info(f"[WORKER] Found {len(pending_videos)} pending videos")
                
                for media in pending_videos:
                    media.pose_analysis_status = "processing"
                    pending_jobs.append({"id": media.id, "s3_key": media.s3_key})
                
                await db.commit()
                # DB session is now released!
            
            # Step 2: Process each video (CPU-heavy, NO DB session held)
            s3_service = get_s3_service()
            pose_service = get_pose_detection_service()
            
            for job in pending_jobs:
                media_id = job["id"]
                s3_key = job["s3_key"]
                
                try:
                    logger.info(f"[WORKER] ▶ Starting pose detection for video {media_id}")
                    
                    # Small delay to ensure S3 finalized the file (multipart uploads)
                    await asyncio.sleep(2)
                    
                    presigned_url = s3_service.generate_presigned_download_url(
                        s3_key=s3_key,
                        expires_in=3600
                    )
                    
                    # Run in thread pool — does NOT block the event loop
                    pose_data = await asyncio.to_thread(
                        pose_service.analyze_video_from_s3,
                        s3_url=presigned_url,
                        fps=10.0,
                        max_frames=1200,
                        max_duration=120.0,
                        min_confidence=0.25
                    )
                    
                    # Step 3: Save results (quick DB op)
                    async with SessionLocal() as db:
                        result = await db.execute(
                            select(MediaUpload).filter(MediaUpload.id == media_id)
                        )
                        media = result.scalar_one_or_none()
                        if media:
                            media.pose_data = pose_data
                            media.pose_analysis_status = "completed"
                            await db.commit()
                    
                    frames = pose_data.get("summary", {}).get("total_frames", "?")
                    confidence = pose_data.get("summary", {}).get("average_confidence", "?")
                    logger.info(f"[WORKER] ✓ Completed video {media_id} — {frames} frames, confidence: {confidence}")
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"[WORKER] ✗ Failed video {media_id}: {error_msg}")
                    
                    # Provide helpful context for common errors
                    if "incomplete or corrupted" in error_msg.lower():
                        logger.error(f"[WORKER] 💡 TIP: Video {media_id} upload may not have completed. Client should wait before confirming.")
                    elif "timeout" in error_msg.lower():
                        logger.error(f"[WORKER] 💡 TIP: Network timeout for video {media_id}. Will retry on next worker cycle.")
                    
                    # Save failure (quick DB op)
                    async with SessionLocal() as db:
                        result = await db.execute(
                            select(MediaUpload).filter(MediaUpload.id == media_id)
                        )
                        media = result.scalar_one_or_none()
                        if media:
                            media.pose_analysis_status = "failed"
                            media.pose_data = {
                                "error": error_msg,
                                "processed_at": datetime.now(timezone.utc).isoformat()
                            }
                            await db.commit()
                        
        except Exception as e:
            logger.error(f"[WORKER] Error in process_pending_videos: {e}", exc_info=True)
    
    async def run(self):
        """Main worker loop."""
        self.running = True
        logger.info(f"[WORKER] Pose detection worker started (interval={self.interval}s)")
        
        while self.running:
            try:
                await self.process_pending_videos()
            except Exception as e:
                logger.error(f"[WORKER] Error in worker loop: {e}")
            
            await asyncio.sleep(self.interval)
        
        logger.info("[WORKER] Pose detection worker stopped")
    
    def start(self):
        """Start the worker in the background."""
        if not self.task:
            try:
                self.task = asyncio.create_task(self.run())
                logger.info(f"[WORKER] ✓ Background worker task created (polling every {self.interval}s)")
                logger.info(f"[WORKER] ✓ Worker will process up to {self.batch_size} videos per batch")
            except RuntimeError as e:
                logger.error(f"[WORKER] ✗ Failed to create worker task: {e}")
                logger.error(f"[WORKER] ✗ This usually means no event loop is running")
                raise
    
    async def stop(self):
        """Stop the worker gracefully."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            logger.info("[WORKER] Worker stopped")


# Global worker instance
_worker = None


def get_worker() -> PoseDetectionWorker:
    """Get the global worker instance."""
    global _worker
    if _worker is None:
        _worker = PoseDetectionWorker(interval=10, batch_size=3)
    return _worker
