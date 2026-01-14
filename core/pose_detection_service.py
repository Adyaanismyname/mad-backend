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
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

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
        logger.info("PoseDetectionService initialized")
    
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
        """Get video metadata using ffprobe."""
        ffprobe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration,r_frame_rate',
            '-of', 'json',
            s3_url
        ]
        
        result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, timeout=30)
        probe_data = json.loads(result.stdout)
        stream_info = probe_data.get('streams', [{}])[0]
        
        return {
            'width': int(stream_info.get('width', 640)),
            'height': int(stream_info.get('height', 480)),
            'duration': float(stream_info.get('duration', 0))
        }
    
    def _extract_frames(self, s3_url: str, video_info: Dict, fps: float, max_frames: int) -> List[Dict]:
        """Extract frames from video using FFmpeg streaming."""
        width, height = video_info['width'], video_info['height']
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', s3_url,
            '-vf', f'fps={fps}',
            '-f', 'image2pipe',
            '-pix_fmt', 'rgb24',
            '-vcodec', 'rawvideo',
            '-loglevel', 'error',
            '-'
        ]
        
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10**8
        )
        
        frames_data = []
        frame_size = width * height * 3
        frame_count = 0
        
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
        
        process.terminate()
        process.wait(timeout=5)
        
        return frames_data
    
    def analyze_video_from_s3(
        self,
        s3_url: str,
        fps: float = 3.0,
        max_frames: int = 60,
        min_confidence: float = 0.2
    ) -> Dict[str, Any]:
        """
        Analyze pose in a video streamed from S3.
        
        All keypoint coordinates are NORMALIZED (0-1 range).
        To get pixel coordinates: x_pixel = x * video_width, y_pixel = y * video_height
        
        Args:
            s3_url: Presigned S3 URL for the video
            fps: Frames per second to analyze (default: 3)
            max_frames: Maximum frames to process (default: 60)
            min_confidence: Minimum confidence threshold (default: 0.2)
        
        Returns:
            Pose data dict with normalized coordinates
        """
        logger.info(f"Starting pose analysis (fps={fps}, max_frames={max_frames})")
        
        # Get video info
        video_info = self._get_video_info(s3_url)
        logger.info(f"Video: {video_info['width']}x{video_info['height']}, duration: {video_info['duration']}s")
        
        # Extract frames
        frames_data = self._extract_frames(s3_url, video_info, fps, max_frames)
        
        if not frames_data:
            raise Exception("No frames could be extracted from the video")
        
        logger.info(f"Extracted {len(frames_data)} frames, running pose detection...")
        
        # Process each frame
        pose_frames = []
        all_confidences = []
        
        for frame_data in frames_data:
            try:
                pose_result = self._detect_pose_single_frame(frame_data['frame'])
                
                # Filter keypoints by confidence
                filtered_keypoints = {
                    name: kp for name, kp in pose_result['keypoints'].items()
                    if kp['confidence'] >= min_confidence
                }
                
                if filtered_keypoints:
                    pose_frames.append({
                        'timestamp': frame_data['timestamp'],
                        'frame_number': frame_data['frame_number'],
                        'keypoints': filtered_keypoints,
                        'confidence': pose_result['confidence']
                    })
                    all_confidences.append(pose_result['confidence'])
                    
            except Exception as e:
                logger.warning(f"Failed to process frame {frame_data['frame_number']}: {e}")
        
        if not pose_frames:
            raise Exception("Failed to detect pose in any frame")
        
        avg_confidence = sum(all_confidences) / len(all_confidences)
        
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
