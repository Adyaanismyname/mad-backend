"""
Pose Detection Service using TensorFlow MoveNet.

This module provides real-time pose detection by streaming video from S3,
extracting frames, and running pose detection using TensorFlow's MoveNet model.

MoveNet is chosen for its:
- Speed: Single pose detection in under 10ms
- Accuracy: State-of-the-art performance
- Robustness: Works well with various poses and lighting conditions

All coordinates are NORMALIZED (0-1 range) so frontend can scale to any video size.
"""

import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import subprocess
import json
import logging
import shutil
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from core.config import settings

logger = logging.getLogger(__name__)

# MoveNet keypoint names
KEYPOINT_NAMES = [
    'nose',
    'left_eye',
    'right_eye',
    'left_ear',
    'right_ear',
    'left_shoulder',
    'right_shoulder',
    'left_elbow',
    'right_elbow',
    'left_wrist',
    'right_wrist',
    'left_hip',
    'right_hip',
    'left_knee',
    'right_knee',
    'left_ankle',
    'right_ankle'
]

# Skeleton connections for visualization
SKELETON_CONNECTIONS = [
    ['nose', 'left_eye'],
    ['nose', 'right_eye'],
    ['left_eye', 'left_ear'],
    ['right_eye', 'right_ear'],
    ['left_shoulder', 'right_shoulder'],
    ['left_shoulder', 'left_elbow'],
    ['right_shoulder', 'right_elbow'],
    ['left_elbow', 'left_wrist'],
    ['right_elbow', 'right_wrist'],
    ['left_shoulder', 'left_hip'],
    ['right_shoulder', 'right_hip'],
    ['left_hip', 'right_hip'],
    ['left_hip', 'left_knee'],
    ['right_hip', 'right_knee'],
    ['left_knee', 'left_ankle'],
    ['right_knee', 'right_ankle']
]


class PoseDetectionService:
    """
    Pose detection service using TensorFlow's MoveNet Lightning model.
    
    MoveNet Lightning is used for speed - suitable for on-demand processing.
    All coordinates are normalized (0-1) for easy frontend scaling.
    """
    
    # MoveNet model URL - using Lightning for speed
    MOVENET_LIGHTNING_URL = "https://tfhub.dev/google/movenet/singlepose/lightning/4"
    
    def __init__(self):
        """Initialize the pose detection service."""
        self._model = None
        self._movenet = None
        self.input_size = 192  # Lightning model input size
        self.ffmpeg_path = settings.FFMPEG_PATH
        self.ffprobe_path = settings.FFPROBE_PATH
        self._check_ffmpeg_availability()
        logger.info("PoseDetectionService initialized")
    
    def _check_ffmpeg_availability(self) -> None:
        """Check if FFmpeg and FFprobe are available."""
        ffmpeg_available = shutil.which(self.ffmpeg_path) is not None
        ffprobe_available = shutil.which(self.ffprobe_path) is not None
        
        if not ffmpeg_available:
            logger.warning(
                f"FFmpeg not found at '{self.ffmpeg_path}'. "
                "Please install FFmpeg or set FFMPEG_PATH in .env file. "
            )
        
        if not ffprobe_available:
            logger.warning(
                f"FFprobe not found at '{self.ffprobe_path}'. "
                "Please install FFmpeg (includes FFprobe) or set FFPROBE_PATH in .env file. "
            )
    
    @property
    def model(self):
        """Lazy load the model on first access."""
        if self._model is None:
            logger.info("Loading MoveNet Lightning model...")
            self._model = hub.load(self.MOVENET_LIGHTNING_URL)
            self._movenet = self._model.signatures['serving_default']
            logger.info("MoveNet model loaded successfully")
        return self._movenet
    
    def _preprocess_frame(self, frame: np.ndarray) -> tf.Tensor:
        """Preprocess a frame for MoveNet input."""
        img = tf.image.resize_with_pad(frame, self.input_size, self.input_size)
        img = tf.cast(img, dtype=tf.int32)
        return tf.expand_dims(img, axis=0)
    
    def _detect_pose_single_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Detect pose keypoints in a single frame.
        
        Returns keypoints with NORMALIZED coordinates (0-1 range).
        """
        input_tensor = self._preprocess_frame(frame)
        outputs = self.model(input_tensor)
        keypoints_with_scores = outputs['output_0'].numpy()[0, 0]
        
        keypoints = {}
        for idx, name in enumerate(KEYPOINT_NAMES):
            y, x, confidence = keypoints_with_scores[idx]
            # Keep coordinates normalized (0-1) - DO NOT multiply by dimensions
            keypoints[name] = {
                'x': round(float(x), 4),  # Normalized 0-1
                'y': round(float(y), 4),  # Normalized 0-1
                'confidence': round(float(confidence), 3)
            }
        
        confidences = [kp['confidence'] for kp in keypoints.values()]
        avg_confidence = sum(confidences) / len(confidences)
        
        return {
            'keypoints': keypoints,
            'confidence': round(avg_confidence, 3)
        }
    
    def _get_video_info(self, s3_url: str) -> Dict[str, Any]:
        """Get video metadata using ffprobe with optimized settings for fast S3 probing."""
        logger.info("[POSE] 📊 Stage 1/3: Fetching video metadata...")
        
        if not shutil.which(self.ffprobe_path):
            raise FileNotFoundError(
                f"FFprobe executable not found at '{self.ffprobe_path}'. "
                "Set FFPROBE_PATH in your .env file to the full path of ffprobe.exe"
            )
        
        # Optimized ffprobe command for fast S3 probing
        # -probesize 5M: Only read first 5MB (default is 5MB but explicit is better)
        # -analyzeduration 5M: Analyze only first 5 seconds of data
        # This makes probing S3 URLs much faster
        ffprobe_cmd = [
            self.ffprobe_path,
            '-v', 'error',
            '-probesize', '5M',  # Limit probe data size for speed
            '-analyzeduration', '5M',  # Limit analysis duration for speed
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration,r_frame_rate',
            '-of', 'json',
            s3_url
        ]
        
        try:
            # Increased timeout to 120s for large videos or slow connections
            result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, timeout=120, check=True)
        except subprocess.TimeoutExpired:
            logger.error(f"FFprobe timeout after 120s for URL: {s3_url[:100]}...")
            raise Exception("Video probing timed out. Video may be too large or network connection is slow.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr or ""
            
            # Check for common errors
            if "moov atom not found" in stderr:
                raise Exception(
                    "Video file is incomplete or corrupted. The upload may not have finished. "
                    "Please try uploading again and ensure the upload completes fully before moving to the next step."
                )
            elif "Connection" in stderr and "timed out" in stderr:
                raise Exception(
                    "Network timeout while connecting to S3. This could be a temporary network issue. "
                    "Try again in a few moments."
                )
            elif "Invalid data found" in stderr:
                raise Exception(
                    "Video file format is invalid or corrupted. Please ensure you're uploading a valid video file."
                )
            else:
                raise Exception(f"FFprobe failed: {stderr}")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"FFprobe executable not found. Please install FFmpeg and ensure it's in your PATH. "
                f"Tried to execute: {self.ffprobe_path}"
            )
        probe_data = json.loads(result.stdout)
        stream_info = probe_data.get('streams', [{}])[0]
        
        video_info = {
            'width': int(stream_info.get('width', 640)),
            'height': int(stream_info.get('height', 480)),
            'duration': float(stream_info.get('duration', 0))
        }
        
        logger.info(f"[POSE] ✓ Metadata fetched: {video_info['width']}x{video_info['height']}, {video_info['duration']:.1f}s")
        return video_info
    
    def _extract_frames(self, s3_url: str, video_info: Dict, fps: float, max_frames: int, max_duration: float = None) -> List[Dict]:
        """Extract frames from video using FFmpeg streaming with optimization."""
        logger.info("[POSE] 🎬 Stage 2/3: Extracting frames from video...")
        
        if not shutil.which(self.ffmpeg_path):
            raise FileNotFoundError(
                f"FFmpeg executable not found at '{self.ffmpeg_path}'. "
                "Set FFMPEG_PATH in your .env file to the full path of ffmpeg.exe"
            )
        
        width, height = video_info['width'], video_info['height']
        video_duration = video_info.get('duration', 0)
        
        # Use full video duration, capped by max_duration if provided
        # If video duration unknown, fall back to max_frames / fps
        if video_duration > 0:
            process_duration = min(video_duration, max_duration) if max_duration else video_duration
        else:
            process_duration = max_duration if max_duration else (max_frames / fps)
        
        logger.info(f"[POSE] Processing {process_duration:.1f}s of video at {fps} fps")
        
        # Robust frame extraction with mobile video support
        # -protocol_whitelist: Allow file,http,https,tcp,tls protocols for S3
        # -reconnect: Auto-reconnect on network issues
        # -an: Disable audio (not needed for pose detection)
        ffmpeg_cmd = [
            self.ffmpeg_path,
            '-protocol_whitelist', 'file,http,https,tcp,tls',
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '5',
            '-i', s3_url,
            '-t', str(process_duration),  # Process full duration (or capped)
            '-vf', f'fps={fps}',  # Extract at specified FPS
            '-f', 'image2pipe',
            '-pix_fmt', 'rgb24',
            '-vcodec', 'rawvideo',
            '-an',  # Disable audio
            '-loglevel', 'warning',  # Show warnings to help debug
            '-'
        ]
        
        try:
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8
            )
        except FileNotFoundError:
            raise FileNotFoundError(
                f"FFmpeg executable not found. Please install FFmpeg and ensure it's in your PATH. "
                f"Tried to execute: {self.ffmpeg_path}"
            )
        
        frames_data = []
        frame_size = width * height * 3
        frame_count = 0
        
        logger.info(f"[POSE] Extracting up to {max_frames} frames at {fps} fps...")
        
        try:
            while frame_count < max_frames:
                raw_frame = process.stdout.read(frame_size)
                if len(raw_frame) < frame_size:
                    break
                
                frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((height, width, 3))
                frames_data.append({
                    'frame': frame,
                    'timestamp': round(frame_count / fps, 3),
                    'frame_number': frame_count
                })
                frame_count += 1
                
                # Log extraction progress every 10%
                if frame_count % max(1, max_frames // 10) == 0:
                    progress = (frame_count / max_frames) * 100
                    logger.info(f"[POSE] Extracting... {frame_count}/{max_frames} frames ({progress:.0f}%)")
        finally:
            # Capture any error output from ffmpeg
            stderr_output = None
            if process.stderr:
                stderr_output = process.stderr.read().decode('utf-8', errors='ignore')
            
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            # Log ffmpeg errors if no frames extracted
            if not frames_data and stderr_output:
                logger.error(f"[POSE] FFmpeg stderr: {stderr_output}")
                raise Exception(f"FFmpeg failed to extract frames. Error: {stderr_output[:500]}")
        
        logger.info(f"[POSE] Successfully extracted {len(frames_data)} frames")
        return frames_data
    
    def analyze_video_from_s3(
        self,
        s3_url: str,
        fps: float = 10.0,
        max_frames: int = 1200,
        max_duration: float = 120.0,
        min_confidence: float = 0.2
    ) -> Dict[str, Any]:
        """
        Analyze pose in a video streamed from S3.
        
        All keypoint coordinates are NORMALIZED (0-1 range).
        To get pixel coordinates: x_pixel = x * video_width, y_pixel = y * video_height
        
        Args:
            s3_url: Presigned S3 URL for the video
            fps: Frames per second to analyze (default: 10 for smooth playback)
            max_frames: Maximum frames to process (default: 1200 = 2 min at 10fps)
            max_duration: Maximum video duration to process in seconds (default: 120s)
            min_confidence: Minimum confidence threshold (default: 0.2)
        
        Returns:
            Pose data dict with normalized coordinates
        """
        logger.info(f"Starting pose analysis (fps={fps}, max_duration={max_duration}s, max_frames={max_frames})")
        
        # Get video info
        video_info = self._get_video_info(s3_url)
        video_duration = video_info.get('duration', 0)
        logger.info(f"Video: {video_info['width']}x{video_info['height']}, duration: {video_duration}s")
        
        # Calculate how many frames we'll actually need for this video
        effective_duration = min(video_duration, max_duration) if video_duration > 0 else max_duration
        expected_frames = int(effective_duration * fps)
        actual_max_frames = min(expected_frames, max_frames)
        
        logger.info(f"[POSE] Will process ~{actual_max_frames} frames for {effective_duration:.1f}s of video")
        
        # Extract frames - pass max_duration to process full video
        frames_data = self._extract_frames(s3_url, video_info, fps, actual_max_frames, max_duration)
        
        if not frames_data:
            raise Exception("No frames could be extracted from the video")
        
        logger.info(f"[POSE] ✓ Extracted {len(frames_data)} frames successfully")
        logger.info("[POSE] 🤸 Stage 3/3: Running pose detection on frames...")
        
        # Process frames with early success exit
        pose_frames = []
        all_confidences = []
        consecutive_failures = 0
        max_consecutive_failures = 5  # Stop if 5 consecutive frames fail
        total_frames = len(frames_data)
        log_interval = max(1, total_frames // 10)  # Log progress every 10%
        
        for i, frame_data in enumerate(frames_data):
            # Log progress every 10%
            if i % log_interval == 0:
                progress = ((i + 1) / total_frames) * 100
                detected = len(pose_frames)
                logger.info(f"[POSE] Analyzing... {i+1}/{total_frames} frames ({progress:.0f}%) | {detected} poses detected")
            try:
                pose_result = self._detect_pose_single_frame(frame_data['frame'])
                
                # Filter keypoints by confidence
                filtered_keypoints = {
                    name: kp for name, kp in pose_result['keypoints'].items()
                    if kp['confidence'] >= min_confidence
                }
                
                if filtered_keypoints and pose_result['confidence'] >= min_confidence:
                    pose_frames.append({
                        'timestamp': frame_data['timestamp'],
                        'frame_number': frame_data['frame_number'],
                        'keypoints': filtered_keypoints,
                        'confidence': pose_result['confidence']
                    })
                    all_confidences.append(pose_result['confidence'])
                    consecutive_failures = 0  # Reset on success
                else:
                    consecutive_failures += 1
                    
            except Exception as e:
                logger.warning(f"Failed to process frame {frame_data['frame_number']}: {e}")
                consecutive_failures += 1
            
            # Early exit if too many consecutive failures (e.g., person left frame)
            if consecutive_failures >= max_consecutive_failures and len(pose_frames) >= 10:
                logger.info(f"Early exit: {consecutive_failures} consecutive failures, {len(pose_frames)} frames processed")
                break
        
        if not pose_frames:
            raise Exception("Failed to detect pose in any frame")
        
        avg_confidence = sum(all_confidences) / len(all_confidences)
        detection_rate = len(pose_frames) / len(frames_data)
        
        logger.info(f"[POSE] ✓ Pose detection complete!")
        logger.info(f"[POSE] 📈 Results: {len(pose_frames)}/{len(frames_data)} frames ({detection_rate:.0%}) | Avg confidence: {avg_confidence:.1%}")
        
        # Build pose data structure
        pose_data = {
            'version': '1.0',
            'model': 'movenet_lightning',
            'processed_at': datetime.now(timezone.utc).isoformat(),
            'video_info': {
                'width': video_info['width'],
                'height': video_info['height'],
                'duration': video_info['duration']
            },
            'settings': {
                'fps': fps,
                'frames_analyzed': len(pose_frames),
                'coordinate_system': 'normalized',  # IMPORTANT: 0-1 range
                'coordinate_note': 'Multiply x by video width and y by video height to get pixel coordinates'
            },
            'keypoint_names': KEYPOINT_NAMES,
            'skeleton_connections': SKELETON_CONNECTIONS,
            'summary': {
                'average_confidence': round(avg_confidence, 3),
                'total_frames': len(pose_frames),
                'detection_rate': round(len(pose_frames) / len(frames_data), 3)
            },
            'frames': pose_frames
        }
        
        logger.info(f"Pose analysis complete: {len(pose_frames)} frames, avg confidence: {avg_confidence:.1%}")
        
        return pose_data


# Singleton instance
_pose_service: Optional[PoseDetectionService] = None


def get_pose_detection_service() -> PoseDetectionService:
    """Get or create pose detection service singleton."""
    global _pose_service
    if _pose_service is None:
        _pose_service = PoseDetectionService()
    return _pose_service
