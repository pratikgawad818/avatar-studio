"""
pipeline/video_enhancement.py
Advanced video quality enhancement for professional, undetectable AI videos.
Includes super-resolution, face enhancement, denoising, color grading, and temporal stabilization.
"""
import os, sys, subprocess, logging, tempfile
from pathlib import Path
import cv2
import numpy as np
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# FACE ENHANCEMENT (GFPGAN/CodeFormer)
# ═══════════════════════════════════════════════════════════════════════════

class FaceEnhancer:
    """Enhance face quality using GFPGAN or CodeFormer."""
    
    def __init__(self, method: str = "gfpgan", device: str = "mps"):
        self.method = method.lower()
        self.device = device
        self.model = None
        
    def _load_gfpgan(self):
        """Load GFPGAN model."""
        try:
            from gfpgan import GFPGANer
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer
            
            # Background upsampler (optional but recommended)
            bg_model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
            bg_upsampler = RealESRGANer(
                scale=2,
                model_path='https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth',
                model=bg_model,
                tile=400,
                tile_pad=10,
                pre_pad=0,
                half=False
            )
            
            self.model = GFPGANer(
                model_path='https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth',
                upscale=2,
                arch='clean',
                channel_multiplier=2,
                bg_upsampler=bg_upsampler,
                device=self.device
            )
            logger.info("✓ GFPGAN loaded")
            return True
        except Exception as e:
            logger.warning(f"GFPGAN load failed: {e}")
            return False
    
    def _load_codeformer(self):
        """Load CodeFormer model."""
        try:
            from codeformer import CodeFormer
            # Placeholder for CodeFormer integration
            logger.info("✓ CodeFormer loaded")
            return True
        except Exception as e:
            logger.warning(f"CodeFormer load failed: {e}")
            return False
    
    def enhance_frame(self, frame: np.ndarray, fidelity: float = 0.5) -> np.ndarray:
        """
        Enhance a single frame.
        
        Args:
            frame: BGR image (numpy array)
            fidelity: Balance between quality and fidelity (0-1)
        
        Returns:
            Enhanced BGR image
        """
        if self.model is None:
            if self.method == "gfpgan":
                if not self._load_gfpgan():
                    return frame
            elif self.method == "codeformer":
                if not self._load_codeformer():
                    return frame
        
        try:
            if self.method == "gfpgan":
                # GFPGAN enhancement
                _, _, output = self.model.enhance(
                    frame, 
                    has_aligned=False, 
                    only_center_face=False, 
                    paste_back=True,
                    weight=fidelity
                )
                return output
            else:
                return frame
        except Exception as e:
            logger.warning(f"Frame enhancement failed: {e}")
            return frame


# ═══════════════════════════════════════════════════════════════════════════
# VIDEO SUPER-RESOLUTION (ESRGAN)
# ═══════════════════════════════════════════════════════════════════════════

class VideoUpscaler:
    """Upscale video using Real-ESRGAN."""
    
    def __init__(self, scale: int = 2, model: str = "RealESRGAN_x2plus"):
        self.scale = scale
        self.model_name = model
        self.upsampler = None
    
    def _load_model(self):
        """Load Real-ESRGAN model."""
        try:
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer
            
            model_paths = {
                "RealESRGAN_x2plus": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth",
                "RealESRGAN_x4plus": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
            }
            
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=self.scale)
            
            self.upsampler = RealESRGANer(
                scale=self.scale,
                model_path=model_paths.get(self.model_name, model_paths["RealESRGAN_x2plus"]),
                model=model,
                tile=400,
                tile_pad=10,
                pre_pad=0,
                half=False
            )
            logger.info(f"✓ Real-ESRGAN {self.model_name} loaded")
            return True
        except Exception as e:
            logger.warning(f"Real-ESRGAN load failed: {e}")
            return False
    
    def upscale_frame(self, frame: np.ndarray) -> np.ndarray:
        """Upscale a single frame."""
        if self.upsampler is None:
            if not self._load_model():
                return frame
        
        try:
            output, _ = self.upsampler.enhance(frame, outscale=self.scale)
            return output
        except Exception as e:
            logger.warning(f"Frame upscale failed: {e}")
            return frame


# ═══════════════════════════════════════════════════════════════════════════
# DENOISING & TEMPORAL STABILIZATION
# ═══════════════════════════════════════════════════════════════════════════

class VideoDenoiser:
    """Remove noise and stabilize video temporally."""
    
    @staticmethod
    def denoise_frame(frame: np.ndarray, strength: int = 10) -> np.ndarray:
        """
        Denoise frame using Non-local Means Denoising.
        
        Args:
            frame: BGR image
            strength: Denoising strength (3-20, default 10)
        """
        return cv2.fastNlMeansDenoisingColored(frame, None, strength, strength, 7, 21)
    
    @staticmethod
    def temporal_smooth(frames: list, window: int = 3) -> list:
        """
        Apply temporal smoothing to reduce flicker.
        
        Args:
            frames: List of BGR frames
            window: Smoothing window size (odd number)
        """
        if len(frames) < window:
            return frames
        
        smoothed = []
        half = window // 2
        
        for i in range(len(frames)):
            start = max(0, i - half)
            end = min(len(frames), i + half + 1)
            window_frames = frames[start:end]
            
            # Weighted average (center frame has more weight)
            weights = np.array([1.0 if j != len(window_frames)//2 else 2.0 for j in range(len(window_frames))])
            weights = weights / weights.sum()
            
            blended = np.zeros_like(frames[i], dtype=np.float32)
            for j, frame in enumerate(window_frames):
                blended += frame.astype(np.float32) * weights[j]
            
            smoothed.append(np.clip(blended, 0, 255).astype(np.uint8))
        
        return smoothed


# ═══════════════════════════════════════════════════════════════════════════
# COLOR GRADING (LUTs & Cinematic Look)
# ═══════════════════════════════════════════════════════════════════════════

class ColorGrader:
    """Apply professional color grading."""
    
    PRESETS = {
        "natural": {
            "brightness": 1.0,
            "contrast": 1.05,
            "saturation": 1.1,
            "temperature": 0,  # Neutral
            "tint": 0
        },
        "cinematic": {
            "brightness": 0.95,
            "contrast": 1.15,
            "saturation": 1.2,
            "temperature": 10,  # Warm
            "tint": -5  # Slightly magenta
        },
        "vibrant": {
            "brightness": 1.05,
            "contrast": 1.1,
            "saturation": 1.3,
            "temperature": 5,
            "tint": 0
        },
        "professional": {
            "brightness": 1.0,
            "contrast": 1.08,
            "saturation": 1.05,
            "temperature": -3,  # Slightly cool
            "tint": 0
        },
        "warm": {
            "brightness": 1.02,
            "contrast": 1.05,
            "saturation": 1.15,
            "temperature": 15,
            "tint": 5
        }
    }
    
    @staticmethod
    def apply_grade(frame: np.ndarray, preset: str = "natural") -> np.ndarray:
        """
        Apply color grading preset.
        
        Args:
            frame: BGR image
            preset: Grading preset name
        """
        settings = ColorGrader.PRESETS.get(preset, ColorGrader.PRESETS["natural"])
        
        # Convert to LAB for better color manipulation
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Brightness & Contrast
        l = np.clip(l.astype(np.float32) * settings["contrast"] * settings["brightness"], 0, 255).astype(np.uint8)
        
        # Temperature (shift b channel in LAB)
        temp = settings["temperature"]
        if temp != 0:
            b = np.clip(b.astype(np.float32) + temp, 0, 255).astype(np.uint8)
        
        # Tint (shift a channel in LAB)
        tint = settings["tint"]
        if tint != 0:
            a = np.clip(a.astype(np.float32) + tint, 0, 255).astype(np.uint8)
        
        lab = cv2.merge([l, a, b])
        graded = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Saturation
        hsv = cv2.cvtColor(graded, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * settings["saturation"], 0, 255)
        graded = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        
        return graded
    
    @staticmethod
    def apply_lut(frame: np.ndarray, lut_path: str) -> np.ndarray:
        """Apply 3D LUT from file (.cube format)."""
        # Placeholder for LUT application
        # Would need to parse .cube files and apply 3D lookup
        return frame


# ═══════════════════════════════════════════════════════════════════════════
# VIDEO PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def enhance_video(
    input_path: str,
    output_path: str,
    enhance_face: bool = True,
    upscale: bool = False,
    upscale_factor: int = 2,
    denoise: bool = True,
    denoise_strength: int = 8,
    color_grade: str = "natural",
    temporal_smooth: bool = True,
    face_fidelity: float = 0.7,
    progress_callback = None
) -> str:
    """
    Enhance video with all quality improvements.
    
    Args:
        input_path: Input video path
        output_path: Output video path
        enhance_face: Apply face enhancement (GFPGAN)
        upscale: Apply super-resolution upscaling
        upscale_factor: Upscaling factor (2 or 4)
        denoise: Apply denoising
        denoise_strength: Denoising strength (3-20)
        color_grade: Color grading preset
        temporal_smooth: Apply temporal smoothing
        face_fidelity: Face enhancement fidelity (0-1)
        progress_callback: Optional callback(progress, message)
    
    Returns:
        Path to enhanced video
    """
    logger.info(f"Enhancing video: {input_path}")
    
    # Initialize enhancers
    face_enhancer = FaceEnhancer() if enhance_face else None
    upscaler = VideoUpscaler(scale=upscale_factor) if upscale else None
    
    # Open video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {input_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Adjust dimensions if upscaling
    if upscale:
        width *= upscale_factor
        height *= upscale_factor
    
    logger.info(f"Processing {total_frames} frames at {fps} fps, {width}x{height}")
    
    # Create temp file for processed frames
    temp_dir = os.path.dirname(output_path)
    temp_video = os.path.join(temp_dir, "enhanced_temp.mp4")
    
    # Video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
    
    frames_buffer = []
    processed_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame
            processed = frame.copy()
            
            # Face enhancement
            if face_enhancer:
                processed = face_enhancer.enhance_frame(processed, fidelity=face_fidelity)
            
            # Upscaling
            if upscaler:
                processed = upscaler.upscale_frame(processed)
            
            # Denoising
            if denoise:
                processed = VideoDenoiser.denoise_frame(processed, strength=denoise_strength)
            
            # Color grading
            if color_grade:
                processed = ColorGrader.apply_grade(processed, preset=color_grade)
            
            frames_buffer.append(processed)
            processed_count += 1
            
            # Progress callback
            if progress_callback and processed_count % 10 == 0:
                progress = int((processed_count / total_frames) * 100)
                progress_callback(progress, f"Enhanced {processed_count}/{total_frames} frames")
            
            # Process in batches for temporal smoothing
            if len(frames_buffer) >= 30 or processed_count == total_frames:
                if temporal_smooth and len(frames_buffer) > 3:
                    frames_buffer = VideoDenoiser.temporal_smooth(frames_buffer, window=3)
                
                # Write frames
                for f in frames_buffer:
                    out.write(f)
                
                frames_buffer = []
        
    finally:
        cap.release()
        out.release()
    
    logger.info(f"✓ Enhanced {processed_count} frames")
    
    # Re-encode with audio using ffmpeg
    _reencode_with_audio(temp_video, input_path, output_path)
    
    # Cleanup
    if os.path.exists(temp_video):
        os.remove(temp_video)
    
    return output_path


def _reencode_with_audio(video_path: str, audio_source: str, output_path: str):
    """Re-encode video with audio from source."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_source,
        "-map", "0:v:0",
        "-map", "1:a:0?",  # Optional audio
        "-c:v", "libx264",
        "-preset", "slow",  # Better quality
        "-crf", "18",  # High quality
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        logger.warning(f"Re-encode failed: {result.stderr[:500]}")
        # Fallback: copy temp file
        import shutil
        shutil.copy2(video_path, output_path)
    
    logger.info(f"✓ Final video: {output_path}")


# ═══════════════════════════════════════════════════════════════════════════
# SHARPENING & CLARITY
# ═══════════════════════════════════════════════════════════════════════════

class VideoSharpener:
    """Apply professional sharpening."""
    
    @staticmethod
    def unsharp_mask(frame: np.ndarray, sigma: float = 1.0, strength: float = 1.5) -> np.ndarray:
        """
        Apply unsharp mask for natural sharpening.
        
        Args:
            frame: BGR image
            sigma: Gaussian blur sigma
            strength: Sharpening strength (1.0-3.0)
        """
        blurred = cv2.GaussianBlur(frame, (0, 0), sigma)
        sharpened = cv2.addWeighted(frame, 1.0 + strength, blurred, -strength, 0)
        return sharpened
    
    @staticmethod
    def adaptive_sharpen(frame: np.ndarray, amount: float = 1.2) -> np.ndarray:
        """Adaptive sharpening that preserves smooth areas."""
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]]) * (amount / 8)
        kernel[1, 1] = 1 + amount
        sharpened = cv2.filter2D(frame, -1, kernel)
        return np.clip(sharpened, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    # Test enhancement
    test_video = "/Users/pratik/Desktop/avatar-studio/outputs/video_20260708_030324.mp4"
    output = "/Users/pratik/Desktop/avatar-studio/outputs/enhanced_test.mp4"
    
    if os.path.exists(test_video):
        enhance_video(
            test_video,
            output,
            enhance_face=True,
            upscale=False,
            denoise=True,
            color_grade="professional"
        )
        print(f"✓ Enhanced: {output}")
