"""
pipeline/lip_sync_advanced.py
Advanced lip-sync with pre/post-processing for ultra-realistic results.
Includes face detection optimization, mouth region enhancement, and temporal smoothing.
"""
import os, sys, subprocess, logging, cv2, numpy as np
from pathlib import Path
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)

WAV2LIP_DIR = Path(__file__).parent.parent / "models" / "Wav2Lip"
CHECKPOINT = WAV2LIP_DIR / "checkpoints" / "wav2lip_gan.pth"


# ═══════════════════════════════════════════════════════════════════════════
# FACE DETECTION & ALIGNMENT
# ═══════════════════════════════════════════════════════════════════════════

class FaceDetector:
    """Advanced face detection and alignment."""
    
    def __init__(self):
        self.detector = None
        self.predictor = None
    
    def _load_dlib(self):
        """Load dlib face detector and predictor."""
        try:
            import dlib
            self.detector = dlib.get_frontal_face_detector()
            # Download shape predictor if not exists
            predictor_path = WAV2LIP_DIR / "shape_predictor_68_face_landmarks.dat"
            if predictor_path.exists():
                self.predictor = dlib.shape_predictor(str(predictor_path))
            logger.info("✓ dlib face detector loaded")
            return True
        except Exception as e:
            logger.warning(f"dlib load failed: {e}")
            return False
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in frame.
        
        Returns:
            List of (x, y, w, h) bounding boxes
        """
        if self.detector is None:
            self._load_dlib()
        
        if self.detector:
            try:
                import dlib
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.detector(gray, 1)
                return [(f.left(), f.top(), f.width(), f.height()) for f in faces]
            except Exception:
                pass
        
        # Fallback to OpenCV
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        return [(int(x), int(y), int(w), int(h)) for x, y, w, h in faces]
    
    def get_landmarks(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """Get 68 facial landmarks."""
        if self.predictor is None:
            return None
        
        try:
            import dlib
            x, y, w, h = bbox
            rect = dlib.rectangle(x, y, x + w, y + h)
            shape = self.predictor(frame, rect)
            landmarks = np.array([[p.x, p.y] for p in shape.parts()])
            return landmarks
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════════════════════
# MOUTH REGION ENHANCEMENT
# ═══════════════════════════════════════════════════════════════════════════

class MouthEnhancer:
    """Enhance mouth region for better lip-sync quality."""
    
    @staticmethod
    def enhance_mouth_region(frame: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
        """
        Enhance sharpness and contrast in mouth region.
        
        Args:
            frame: BGR image
            landmarks: 68 facial landmarks
        
        Returns:
            Enhanced frame
        """
        # Mouth landmarks are indices 48-67
        mouth_points = landmarks[48:68]
        
        # Get bounding box of mouth with padding
        x_min, y_min = mouth_points.min(axis=0)
        x_max, y_max = mouth_points.max(axis=0)
        
        padding = 20
        x_min = max(0, x_min - padding)
        y_min = max(0, y_min - padding)
        x_max = min(frame.shape[1], x_max + padding)
        y_max = min(frame.shape[0], y_max + padding)
        
        # Extract mouth region
        mouth_region = frame[y_min:y_max, x_min:x_max].copy()
        
        if mouth_region.size == 0:
            return frame
        
        # Enhance contrast
        lab = cv2.cvtColor(mouth_region, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Sharpen
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]]) / 8
        enhanced = cv2.filter2D(enhanced, -1, kernel)
        
        # Blend back
        result = frame.copy()
        result[y_min:y_max, x_min:x_max] = enhanced
        
        return result
    
    @staticmethod
    def smooth_mouth_boundaries(frame: np.ndarray, landmarks: np.ndarray, mask_feather: int = 5) -> np.ndarray:
        """Create smooth blending around mouth region."""
        mouth_points = landmarks[48:68]
        
        # Create mask
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        hull = cv2.convexHull(mouth_points.astype(np.int32))
        cv2.fillConvexPoly(mask, hull, 255)
        
        # Feather edges
        mask = cv2.GaussianBlur(mask, (mask_feather * 2 + 1, mask_feather * 2 + 1), 0)
        
        return mask


# ═══════════════════════════════════════════════════════════════════════════
# PRE-PROCESSING: FACE PREPARATION
# ═══════════════════════════════════════════════════════════════════════════

def preprocess_video_for_lipsync(
    input_video: str,
    output_video: str,
    enhance_face: bool = True,
    stabilize: bool = True
) -> str:
    """
    Pre-process video before Wav2Lip for better results.
    
    Args:
        input_video: Input video path
        output_video: Output video path
        enhance_face: Apply face enhancement
        stabilize: Apply face stabilization
    
    Returns:
        Path to preprocessed video
    """
    logger.info("Pre-processing video for lip-sync...")
    
    cap = cv2.VideoCapture(input_video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    
    face_detector = FaceDetector()
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            processed = frame.copy()
            
            if enhance_face:
                # Detect face
                faces = face_detector.detect_faces(frame)
                
                if faces:
                    x, y, w, h = faces[0]  # Use first face
                    
                    # Get landmarks
                    landmarks = face_detector.get_landmarks(frame, (x, y, w, h))
                    
                    if landmarks is not None:
                        # Enhance mouth region
                        processed = MouthEnhancer.enhance_mouth_region(processed, landmarks)
            
            out.write(processed)
            frame_count += 1
    
    finally:
        cap.release()
        out.release()
    
    logger.info(f"✓ Pre-processed {frame_count} frames")
    return output_video


# ═══════════════════════════════════════════════════════════════════════════
# POST-PROCESSING: BLEND & SMOOTH
# ═══════════════════════════════════════════════════════════════════════════

class LipsyncPostProcessor:
    """Post-process Wav2Lip output for seamless integration."""
    
    @staticmethod
    def blend_mouth_region(
        original_frame: np.ndarray,
        lipsync_frame: np.ndarray,
        landmarks: np.ndarray,
        blend_strength: float = 0.85
    ) -> np.ndarray:
        """
        Blend lip-synced mouth back into original frame smoothly.
        
        Args:
            original_frame: Original frame
            lipsync_frame: Wav2Lip output frame
            landmarks: Facial landmarks
            blend_strength: Blend strength (0-1)
        
        Returns:
            Blended frame
        """
        if landmarks is None:
            return lipsync_frame
        
        # Create mouth mask
        mouth_points = landmarks[48:68]
        mask = np.zeros(original_frame.shape[:2], dtype=np.float32)
        hull = cv2.convexHull(mouth_points.astype(np.int32))
        cv2.fillConvexPoly(mask, hull, 1.0)
        
        # Feather edges for smooth blending
        mask = cv2.GaussianBlur(mask, (15, 15), 5)
        mask = np.expand_dims(mask, axis=2)
        mask = mask * blend_strength
        
        # Blend
        blended = (lipsync_frame * mask + original_frame * (1 - mask)).astype(np.uint8)
        
        return blended
    
    @staticmethod
    def temporal_smoothing(frames: List[np.ndarray], window: int = 5) -> List[np.ndarray]:
        """
        Apply temporal smoothing to reduce jitter in lip movements.
        
        Args:
            frames: List of frames
            window: Smoothing window size
        
        Returns:
            Smoothed frames
        """
        if len(frames) < window:
            return frames
        
        smoothed = []
        half = window // 2
        
        for i in range(len(frames)):
            start = max(0, i - half)
            end = min(len(frames), i + half + 1)
            
            # Weighted average (center frame has highest weight)
            weights = np.array([1.0] * (end - start))
            center_idx = i - start
            if center_idx < len(weights):
                weights[center_idx] = 2.0
            weights = weights / weights.sum()
            
            # Blend frames
            blended = np.zeros_like(frames[i], dtype=np.float32)
            for j, idx in enumerate(range(start, end)):
                blended += frames[idx].astype(np.float32) * weights[j]
            
            smoothed.append(np.clip(blended, 0, 255).astype(np.uint8))
        
        return smoothed
    
    @staticmethod
    def color_match(source: np.ndarray, target: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Match color distribution of source to target.
        
        Args:
            source: Source image (to be adjusted)
            target: Target image (reference)
            mask: Optional mask for region of interest
        
        Returns:
            Color-matched source image
        """
        # Convert to LAB color space
        source_lab = cv2.cvtColor(source, cv2.COLOR_BGR2LAB).astype(np.float32)
        target_lab = cv2.cvtColor(target, cv2.COLOR_BGR2LAB).astype(np.float32)
        
        # Calculate mean and std for each channel
        if mask is not None:
            mask_bool = mask > 0
            source_mean = [source_lab[:, :, i][mask_bool].mean() for i in range(3)]
            source_std = [source_lab[:, :, i][mask_bool].std() for i in range(3)]
            target_mean = [target_lab[:, :, i][mask_bool].mean() for i in range(3)]
            target_std = [target_lab[:, :, i][mask_bool].std() for i in range(3)]
        else:
            source_mean = source_lab.reshape(-1, 3).mean(axis=0)
            source_std = source_lab.reshape(-1, 3).std(axis=0)
            target_mean = target_lab.reshape(-1, 3).mean(axis=0)
            target_std = target_lab.reshape(-1, 3).std(axis=0)
        
        # Match statistics
        result_lab = source_lab.copy()
        for i in range(3):
            if source_std[i] > 0:
                result_lab[:, :, i] = (result_lab[:, :, i] - source_mean[i]) * (target_std[i] / source_std[i]) + target_mean[i]
        
        result_lab = np.clip(result_lab, 0, 255).astype(np.uint8)
        result = cv2.cvtColor(result_lab, cv2.COLOR_LAB2BGR)
        
        return result


def postprocess_lipsync_video(
    original_video: str,
    lipsync_video: str,
    output_video: str,
    blend_strength: float = 0.85,
    temporal_smooth: bool = True,
    color_match: bool = True
) -> str:
    """
    Post-process Wav2Lip output for seamless blending.
    
    Args:
        original_video: Original video path
        lipsync_video: Wav2Lip output video path
        output_video: Final output path
        blend_strength: Blending strength (0-1)
        temporal_smooth: Apply temporal smoothing
        color_match: Match colors between original and lipsync
    
    Returns:
        Path to post-processed video
    """
    logger.info("Post-processing lip-sync video...")
    
    cap_orig = cv2.VideoCapture(original_video)
    cap_sync = cv2.VideoCapture(lipsync_video)
    
    fps = cap_orig.get(cv2.CAP_PROP_FPS)
    width = int(cap_orig.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap_orig.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    
    face_detector = FaceDetector()
    processor = LipsyncPostProcessor()
    frame_buffer = []
    frame_count = 0
    
    try:
        while True:
            ret_orig, frame_orig = cap_orig.read()
            ret_sync, frame_sync = cap_sync.read()
            
            if not (ret_orig and ret_sync):
                break
            
            # Detect face and landmarks
            faces = face_detector.detect_faces(frame_orig)
            landmarks = None
            
            if faces:
                landmarks = face_detector.get_landmarks(frame_orig, faces[0])
            
            # Color matching
            if color_match and landmarks is not None:
                frame_sync = processor.color_match(frame_sync, frame_orig)
            
            # Blend mouth region
            if landmarks is not None:
                blended = processor.blend_mouth_region(frame_orig, frame_sync, landmarks, blend_strength)
            else:
                # Fallback: simple blend
                blended = cv2.addWeighted(frame_orig, 0.3, frame_sync, 0.7, 0)
            
            frame_buffer.append(blended)
            frame_count += 1
            
            # Process in batches for temporal smoothing
            if len(frame_buffer) >= 30 or (not ret_orig or not ret_sync):
                if temporal_smooth and len(frame_buffer) > 5:
                    frame_buffer = processor.temporal_smoothing(frame_buffer, window=5)
                
                for f in frame_buffer:
                    out.write(f)
                
                frame_buffer = []
    
    finally:
        cap_orig.release()
        cap_sync.release()
        out.release()
    
    logger.info(f"✓ Post-processed {frame_count} frames")
    return output_video


# ═══════════════════════════════════════════════════════════════════════════
# ADVANCED WAV2LIP RUNNER
# ═══════════════════════════════════════════════════════════════════════════

def run_wav2lip_advanced(
    face_video: str,
    audio: str,
    output: str,
    quality: str = "enhanced",
    temp_dir: str = "temp",
    batch_size: int = 128,
    preprocess: bool = True,
    postprocess: bool = True
) -> str:
    """
    Run Wav2Lip with advanced pre/post-processing.
    
    Args:
        face_video: Input face video
        audio: Audio file
        output: Final output path
        quality: Quality preset
        temp_dir: Temporary directory
        batch_size: Wav2Lip batch size
        preprocess: Apply pre-processing
        postprocess: Apply post-processing
    
    Returns:
        Path to final video
    """
    os.makedirs(temp_dir, exist_ok=True)
    
    # Pre-process
    preprocessed_video = face_video
    if preprocess:
        preprocessed_video = os.path.join(temp_dir, "preprocessed.mp4")
        preprocess_video_for_lipsync(face_video, preprocessed_video)
    
    # Run Wav2Lip
    from pipeline.lip_sync import run_wav2lip
    lipsync_video = os.path.join(temp_dir, "lipsync_raw.mp4")
    run_wav2lip(preprocessed_video, audio, lipsync_video, quality, temp_dir, batch_size)
    
    # Post-process
    final_video = output
    if postprocess:
        postprocess_lipsync_video(
            preprocessed_video,
            lipsync_video,
            final_video,
            blend_strength=0.85,
            temporal_smooth=True,
            color_match=True
        )
    else:
        import shutil
        shutil.copy2(lipsync_video, final_video)
    
    return final_video


if __name__ == "__main__":
    # Test advanced lip-sync
    logger.setLevel(logging.INFO)
    print("Advanced lip-sync module loaded")
