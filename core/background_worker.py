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
        """Process videos with pending pose analysis status."""
        try:
            async with SessionLocal() as db:
                # Find pending videos
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
                    return
                
                logger.info(f"[WORKER] Processing {len(pending_videos)} pending videos")
                
                s3_service = get_s3_service()
                pose_service = get_pose_detection_service()
                
                for media in pending_videos:
                    try:
                        # Update status to processing
                        media.pose_analysis_status = "processing"
                        await db.commit()
                        
                        # Get presigned URL
                        presigned_url = s3_service.generate_presigned_download_url(
                            s3_key=media.s3_key,
                            expires_in=3600
                        )
                        
                        # Run pose detection - 10fps for smooth playback, up to 2 min videos
                        pose_data = pose_service.analyze_video_from_s3(
                            s3_url=presigned_url,
                            fps=10.0,
                            max_frames=1200,
                            max_duration=120.0,
                            min_confidence=0.25
                        )
                        
                        # Save results
                        media.pose_data = pose_data
                        media.pose_analysis_status = "completed"
                        await db.commit()
                        
                        logger.info(f"[WORKER] ✓ Completed pose detection for video {media.id}")
                        
                    except Exception as e:
                        logger.error(f"[WORKER] ✗ Failed processing video {media.id}: {e}")
                        
                        # Update status to failed
                        media.pose_analysis_status = "failed"
                        media.pose_data = {
                            "error": str(e),
                            "processed_at": datetime.now(timezone.utc).isoformat()
                        }
                        await db.commit()
                        
        except Exception as e:
            logger.error(f"[WORKER] Error in process_pending_videos: {e}")
    
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
            self.task = asyncio.create_task(self.run())
            logger.info("[WORKER] Background worker task created")
    
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
