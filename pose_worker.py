"""
Background worker for processing pose detection on uploaded videos.

This script runs independently from the main FastAPI application and processes
videos with 'pending' pose analysis status.

Usage:
    python pose_worker.py [--interval SECONDS] [--batch-size N]

Options:
    --interval     Seconds to wait between checks (default: 30)
    --batch-size   Number of videos to process per batch (default: 5)
    --once         Process once and exit (don't loop)
"""

import asyncio
import logging
import argparse
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import SessionLocal
from models.media_upload import MediaUpload
from core.s3_service import get_s3_service
from core.pose_detection_service import get_pose_detection_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def process_pending_videos(batch_size: int = 5):
    """Process videos with pending pose analysis status."""
    async with SessionLocal() as db:
        # Find pending videos
        result = await db.execute(
            select(MediaUpload)
            .filter(
                MediaUpload.media_type == "video",
                MediaUpload.pose_analysis_status == "pending",
                MediaUpload.s3_key.isnot(None)
            )
            .limit(batch_size)
        )
        pending_videos = result.scalars().all()
        
        if not pending_videos:
            logger.info("[WORKER] No pending videos to process")
            return 0
        
        logger.info(f"[WORKER] Found {len(pending_videos)} pending videos to process")
        
        processed_count = 0
        s3_service = get_s3_service()
        pose_service = get_pose_detection_service()
        
        for media in pending_videos:
            try:
                logger.info(f"[WORKER] Processing video {media.id}")
                
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
                
                processed_count += 1
                logger.info(f"[WORKER] ✓ Successfully processed video {media.id}")
                
            except Exception as e:
                logger.error(f"[WORKER] ✗ Failed to process video {media.id}: {e}", exc_info=True)
                
                # Update status to failed
                media.pose_analysis_status = "failed"
                media.pose_data = {
                    "error": str(e),
                    "processed_at": datetime.now(timezone.utc).isoformat()
                }
                await db.commit()
        
        logger.info(f"[WORKER] Batch complete: {processed_count}/{len(pending_videos)} successful")
        return processed_count


async def worker_loop(interval: int = 30, batch_size: int = 5):
    """Main worker loop that continuously processes pending videos."""
    logger.info(f"[WORKER] Starting pose detection worker (interval={interval}s, batch_size={batch_size})")
    
    while True:
        try:
            await process_pending_videos(batch_size)
        except Exception as e:
            logger.error(f"[WORKER] Error in worker loop: {e}", exc_info=True)
        
        logger.info(f"[WORKER] Sleeping for {interval} seconds...")
        await asyncio.sleep(interval)


async def run_once(batch_size: int = 5):
    """Process pending videos once and exit."""
    logger.info(f"[WORKER] Running once (batch_size={batch_size})")
    processed = await process_pending_videos(batch_size)
    logger.info(f"[WORKER] Processed {processed} videos. Exiting.")


def main():
    parser = argparse.ArgumentParser(description="Background worker for pose detection")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Seconds to wait between processing batches (default: 30)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of videos to process per batch (default: 5)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process once and exit instead of continuous loop"
    )
    
    args = parser.parse_args()
    
    if args.once:
        asyncio.run(run_once(args.batch_size))
    else:
        asyncio.run(worker_loop(args.interval, args.batch_size))


if __name__ == "__main__":
    main()
