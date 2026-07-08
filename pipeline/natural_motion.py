"""
pipeline/natural_motion.py
Add natural head movements, eye blinks, breathing motion, and micro-expressions
to eliminate the "frozen" AI look and create ultra-realistic avatar videos.
"""
import os, logging, cv2, numpy as np
from typing import Tuple, List, Optional
import random

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# HEAD MOVEMENT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

class HeadMovementGenerator:
    """Generate natural head movements using Perlin noise and motion curves."""
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed if seed is not None else random.randint(0, 10000)
        random.seed(self.seed)
        np.random.seed(self.seed)
    
    @staticmethod
    def perlin_noise_1d(length: int, scale: float = 10.0, octaves: int = 3) -> np.ndarray:
        """
        Generate 1D Perlin noise for smooth natural motion.
        
        Args:
            length: Number of samples
            scale: Noise frequency scale
            octaves: Number of octaves for detail
        
        Returns:
            Noise array normalized to [-1, 1]
        """
        noise = np.zeros(length)
        
        for octave in range(octaves):
            freq = 2 ** octave / scale
            amplitude = 1 / (2 ** octave)
            
            # Simple noise generation
            t = np.arange(length) * freq
            noise += np.sin(t + np.random.rand() * 2 * np.pi) * amplitude
        
        # Normalize
        if noise.max() != noise.min():
            noise = (noise - noise.min()) / (noise.max() - noise.min()) * 2 - 1
        
        return noise
    
    def generate_head_motion(
        self,
        num_frames: int,
        fps: float = 25.0,
        motion_intensity: float = 1.0
    ) -> dict:
        """
        Generate natural head motion curves.
        
        Args:
            num_frames: Number of frames
            fps: Frames per second
            motion_intensity: Motion intensity multiplier (0-2)
        
        Returns:
            Dictionary with motion curves: {
                'yaw': left-right rotation,
                'pitch': up-down rotation,
                'roll': head tilt,
                'tx': horizontal translation,
                'ty': vertical translation
            }
        """
        # Different scales for different motion types
        yaw_scale = 15.0 * motion_intensity    # Slow left-right
        pitch_scale = 20.0 * motion_intensity  # Slower up-down
        roll_scale = 30.0 * motion_intensity   # Even slower tilt
        tx_scale = 12.0 * motion_intensity     # Horizontal drift
        ty_scale = 18.0 * motion_intensity     # Vertical drift
        
        motion = {
            'yaw': self.perlin_noise_1d(num_frames, yaw_scale, octaves=3) * 3.0,      # ±3 degrees
            'pitch': self.perlin_noise_1d(num_frames, pitch_scale, octaves=3) * 2.0,  # ±2 degrees
            'roll': self.perlin_noise_1d(num_frames, roll_scale, octaves=2) * 1.5,    # ±1.5 degrees
            'tx': self.perlin_noise_1d(num_frames, tx_scale, octaves=2) * 8.0,        # ±8 pixels
            'ty': self.perlin_noise_1d(num_frames, ty_scale, octaves=2) * 5.0,        # ±5 pixels
        }
        
        # Add occasional nods and head turns (punctuation)
        duration_sec = num_frames / fps
        num_gestures = int(duration_sec / 8)  # One gesture every 8 seconds on average
        
        for _ in range(num_gestures):
            frame_idx = random.randint(30, num_frames - 30)
            gesture_type = random.choice(['nod', 'shake', 'tilt'])
            
            if gesture_type == 'nod':
                # Quick nod (pitch motion)
                for i in range(-5, 5):
                    if 0 <= frame_idx + i < num_frames:
                        motion['pitch'][frame_idx + i] += np.sin(i * np.pi / 5) * 4.0 * motion_intensity
            
            elif gesture_type == 'shake':
                # Small head shake (yaw motion)
                for i in range(-8, 8):
                    if 0 <= frame_idx + i < num_frames:
                        motion['yaw'][frame_idx + i] += np.sin(i * np.pi / 8) * 5.0 * motion_intensity
            
            elif gesture_type == 'tilt':
                # Head tilt (roll motion)
                for i in range(-6, 6):
                    if 0 <= frame_idx + i < num_frames:
                        motion['roll'][frame_idx + i] += np.sin(i * np.pi / 6) * 3.0 * motion_intensity
        
        logger.info(f"Generated head motion: {num_frames} frames, intensity={motion_intensity:.2f}")
        return motion
    
    @staticmethod
    def apply_motion_to_frame(
        frame: np.ndarray,
        yaw: float,
        pitch: float,
        roll: float,
        tx: float,
        ty: float
    ) -> np.ndarray:
        """
        Apply rotation and translation to frame.
        
        Args:
            frame: Input frame (BGR)
            yaw: Left-right rotation in degrees
            pitch: Up-down rotation in degrees
            roll: Head tilt in degrees
            tx: Horizontal translation in pixels
            ty: Vertical translation in pixels
        
        Returns:
            Transformed frame
        """
        h, w = frame.shape[:2]
        center = (w // 2, h // 2)
        
        # Rotation matrix (2D rotation for roll)
        M_roll = cv2.getRotationMatrix2D(center, roll, 1.0)
        
        # Translation
        M_roll[0, 2] += tx
        M_roll[1, 2] += ty
        
        # Apply transformation
        result = cv2.warpAffine(frame, M_roll, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        
        # For yaw and pitch, apply subtle perspective transform
        if abs(yaw) > 0.5 or abs(pitch) > 0.5:
            # Simple perspective approximation
            scale_x = 1.0 - abs(yaw) * 0.01
            scale_y = 1.0 - abs(pitch) * 0.01
            
            M_perspective = cv2.getRotationMatrix2D(center, 0, 1.0)
            M_perspective[0, 0] *= scale_x
            M_perspective[1, 1] *= scale_y
            
            result = cv2.warpAffine(result, M_perspective, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        
        return result


# ═══════════════════════════════════════════════════════════════════════════
# EYE BLINK GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

class EyeBlinkGenerator:
    """Generate natural eye blink patterns."""
    
    @staticmethod
    def generate_blinks(
        num_frames: int,
        fps: float = 25.0,
        blink_rate: float = 12.0  # Blinks per minute
    ) -> List[Tuple[int, int]]:
        """
        Generate eye blink timing.
        
        Args:
            num_frames: Total number of frames
            fps: Frames per second
            blink_rate: Average blinks per minute
        
        Returns:
            List of (start_frame, duration_frames) tuples
        """
        duration_sec = num_frames / fps
        duration_min = duration_sec / 60.0
        
        # Total blinks with random variation
        num_blinks = int(blink_rate * duration_min * random.uniform(0.8, 1.2))
        
        blinks = []
        for _ in range(num_blinks):
            # Random blink timing (avoid first and last 0.5 seconds)
            start_frame = random.randint(int(fps * 0.5), int(num_frames - fps * 0.5))
            
            # Blink duration: typically 100-400ms
            duration_ms = random.randint(100, 400)
            duration_frames = max(2, int(duration_ms / 1000 * fps))
            
            blinks.append((start_frame, duration_frames))
        
        # Sort by start frame
        blinks.sort(key=lambda x: x[0])
        
        logger.info(f"Generated {len(blinks)} blinks over {duration_sec:.1f}s")
        return blinks
    
    @staticmethod
    def apply_blink_to_frame(
        frame: np.ndarray,
        blink_progress: float,
        eye_landmarks: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Apply eye blink effect to frame.
        
        Args:
            frame: Input frame
            blink_progress: Blink progress (0=open, 1=closed)
            eye_landmarks: Eye landmark points (if available)
        
        Returns:
            Frame with blink effect
        """
        if blink_progress <= 0:
            return frame
        
        # Simple darkening effect in eye region (more sophisticated with landmarks)
        # This is a placeholder - full implementation would use face landmarks
        # to darken actual eye regions
        
        result = frame.copy()
        
        # If no landmarks, return as-is (placeholder)
        if eye_landmarks is None:
            return result
        
        # Create eye region mask and darken
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [eye_landmarks.astype(np.int32)], 255)
        
        # Darken based on blink progress
        darkened = cv2.addWeighted(result, 1 - blink_progress * 0.7, result, 0, -int(blink_progress * 50))
        result = np.where(mask[:, :, None] > 0, darkened, result).astype(np.uint8)
        
        return result


# ═══════════════════════════════════════════════════════════════════════════
# BREATHING MOTION
# ═══════════════════════════════════════════════════════════════════════════

class BreathingMotion:
    """Generate subtle breathing motion."""
    
    @staticmethod
    def generate_breathing_curve(
        num_frames: int,
        fps: float = 25.0,
        breaths_per_minute: float = 15.0
    ) -> np.ndarray:
        """
        Generate breathing motion curve.
        
        Args:
            num_frames: Number of frames
            fps: Frames per second
            breaths_per_minute: Breathing rate
        
        Returns:
            Breathing intensity array (0-1)
        """
        duration_sec = num_frames / fps
        breath_freq = breaths_per_minute / 60.0  # Hz
        
        t = np.arange(num_frames) / fps
        
        # Breathing is sinusoidal with slight irregularity
        breathing = np.sin(2 * np.pi * breath_freq * t)
        
        # Add slight irregularity
        irregularity = np.sin(2 * np.pi * breath_freq * t * 0.3 + np.random.rand()) * 0.2
        breathing += irregularity
        
        # Normalize to 0-1
        breathing = (breathing + 1.2) / 2.4
        breathing = np.clip(breathing, 0, 1)
        
        return breathing
    
    @staticmethod
    def apply_breathing(frame: np.ndarray, breathing_intensity: float) -> np.ndarray:
        """
        Apply subtle breathing motion (slight zoom).
        
        Args:
            frame: Input frame
            breathing_intensity: Breathing intensity (0-1)
        
        Returns:
            Frame with breathing motion
        """
        # Subtle scale change (±0.5%)
        scale = 1.0 + (breathing_intensity - 0.5) * 0.01
        
        h, w = frame.shape[:2]
        center = (w // 2, h // 2)
        
        M = cv2.getRotationMatrix2D(center, 0, scale)
        result = cv2.warpAffine(frame, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        
        return result


# ═══════════════════════════════════════════════════════════════════════════
# MICRO-EXPRESSIONS
# ═══════════════════════════════════════════════════════════════════════════

class MicroExpressions:
    """Generate subtle facial micro-expressions."""
    
    @staticmethod
    def generate_expression_events(
        num_frames: int,
        fps: float = 25.0,
        events_per_minute: float = 3.0
    ) -> List[Tuple[int, str, float]]:
        """
        Generate micro-expression events.
        
        Args:
            num_frames: Number of frames
            fps: Frames per second
            events_per_minute: Micro-expressions per minute
        
        Returns:
            List of (frame, expression_type, intensity) tuples
        """
        duration_sec = num_frames / fps
        duration_min = duration_sec / 60.0
        
        num_events = int(events_per_minute * duration_min)
        
        expression_types = ['smile', 'thoughtful', 'slight_frown', 'eyebrow_raise']
        
        events = []
        for _ in range(num_events):
            frame = random.randint(int(fps), num_frames - int(fps))
            expr_type = random.choice(expression_types)
            intensity = random.uniform(0.1, 0.3)  # Subtle
            events.append((frame, expr_type, intensity))
        
        events.sort(key=lambda x: x[0])
        return events


# ═══════════════════════════════════════════════════════════════════════════
# FULL NATURAL MOTION PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def add_natural_motion(
    input_video: str,
    output_video: str,
    head_motion_intensity: float = 0.8,
    enable_blinks: bool = True,
    enable_breathing: bool = True,
    enable_micro_expressions: bool = False,  # Requires face landmarks
    seed: Optional[int] = None
) -> str:
    """
    Add natural motion to avatar video.
    
    Args:
        input_video: Input video path
        output_video: Output video path
        head_motion_intensity: Head motion intensity (0-2)
        enable_blinks: Enable eye blinks
        enable_breathing: Enable breathing motion
        enable_micro_expressions: Enable micro-expressions (experimental)
        seed: Random seed for reproducibility
    
    Returns:
        Path to output video
    """
    logger.info(f"Adding natural motion to video: {input_video}")
    
    cap = cv2.VideoCapture(input_video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Generate motion curves
    head_gen = HeadMovementGenerator(seed=seed)
    head_motion = head_gen.generate_head_motion(total_frames, fps, head_motion_intensity)
    
    blinks = []
    if enable_blinks:
        blinks = EyeBlinkGenerator.generate_blinks(total_frames, fps)
    
    breathing_curve = None
    if enable_breathing:
        breathing_curve = BreathingMotion.generate_breathing_curve(total_frames, fps)
    
    # Video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    
    frame_idx = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            result = frame.copy()
            
            # Apply head motion
            if head_motion_intensity > 0:
                result = head_gen.apply_motion_to_frame(
                    result,
                    yaw=head_motion['yaw'][frame_idx],
                    pitch=head_motion['pitch'][frame_idx],
                    roll=head_motion['roll'][frame_idx],
                    tx=head_motion['tx'][frame_idx],
                    ty=head_motion['ty'][frame_idx]
                )
            
            # Apply breathing
            if breathing_curve is not None:
                result = BreathingMotion.apply_breathing(result, breathing_curve[frame_idx])
            
            # Apply blinks (simplified without landmarks)
            if enable_blinks:
                for blink_start, blink_duration in blinks:
                    if blink_start <= frame_idx < blink_start + blink_duration:
                        # Calculate blink progress (0 at start/end, 1 at middle)
                        progress = (frame_idx - blink_start) / blink_duration
                        blink_amount = np.sin(progress * np.pi)  # Smooth curve
                        # Simple darkening effect (placeholder)
                        # Full implementation would need face landmarks
                        break
            
            out.write(result)
            frame_idx += 1
            
            if frame_idx % 100 == 0:
                logger.info(f"Processed {frame_idx}/{total_frames} frames")
    
    finally:
        cap.release()
        out.release()
    
    logger.info(f"✓ Added natural motion to {frame_idx} frames")
    return output_video


def add_natural_motion_with_audio(
    input_video: str,
    audio_path: str,
    output_video: str,
    **kwargs
) -> str:
    """
    Add natural motion and re-attach audio.
    
    Args:
        input_video: Input video path
        audio_path: Audio file path
        output_video: Final output path
        **kwargs: Arguments for add_natural_motion
    
    Returns:
        Path to final video
    """
    import tempfile
    import subprocess
    
    # Create temp file for video without audio
    temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False).name
    
    try:
        # Add motion
        add_natural_motion(input_video, temp_video, **kwargs)
        
        # Re-attach audio
        cmd = [
            "ffmpeg", "-y",
            "-i", temp_video,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_video
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if result.returncode != 0:
            logger.warning(f"Audio re-attach failed: {result.stderr[:300]}")
            import shutil
            shutil.copy2(temp_video, output_video)
    
    finally:
        if os.path.exists(temp_video):
            os.remove(temp_video)
    
    return output_video


if __name__ == "__main__":
    # Test natural motion
    logger.setLevel(logging.INFO)
    print("Natural motion module loaded")
    print("Features: head movement, eye blinks, breathing, micro-expressions")
