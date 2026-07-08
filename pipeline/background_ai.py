"""
pipeline/background_ai.py
AI-powered background removal, generation, and replacement.
Includes segmentation models, virtual backgrounds, and depth-based blur.
"""
import os, logging, subprocess, cv2, numpy as np
from pathlib import Path
from typing import Tuple, Optional, List
import tempfile

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# BACKGROUND REMOVAL (SEGMENTATION)
# ═══════════════════════════════════════════════════════════════════════════

class BackgroundRemover:
    """Remove background using AI segmentation."""
    
    def __init__(self, method: str = "rembg"):
        """
        Initialize background remover.
        
        Args:
            method: Removal method (rembg, mediapipe, u2net)
        """
        self.method = method.lower()
        self.model = None
    
    def _load_rembg(self):
        """Load rembg model (U-2-Net based)."""
        try:
            from rembg import remove, new_session
            self.model = new_session("u2net")
            logger.info("✓ Rembg (U-2-Net) loaded")
            return True
        except Exception as e:
            logger.warning(f"Rembg load failed: {e}")
            return False
    
    def _load_mediapipe(self):
        """Load MediaPipe selfie segmentation."""
        try:
            import mediapipe as mp
            self.model = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
            logger.info("✓ MediaPipe segmentation loaded")
            return True
        except Exception as e:
            logger.warning(f"MediaPipe load failed: {e}")
            return False
    
    def remove_background(
        self,
        image: np.ndarray,
        return_mask: bool = False
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Remove background from image.
        
        Args:
            image: Input image (BGR)
            return_mask: Return segmentation mask
        
        Returns:
            (Image with transparent background, optional mask)
        """
        if self.model is None:
            if self.method == "rembg":
                if not self._load_rembg():
                    raise RuntimeError("Failed to load rembg")
            elif self.method == "mediapipe":
                if not self._load_mediapipe():
                    raise RuntimeError("Failed to load mediapipe")
        
        if self.method == "rembg":
            return self._remove_with_rembg(image, return_mask)
        elif self.method == "mediapipe":
            return self._remove_with_mediapipe(image, return_mask)
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def _remove_with_rembg(
        self,
        image: np.ndarray,
        return_mask: bool
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Remove background using rembg."""
        from rembg import remove
        import io
        from PIL import Image
        
        # Convert to PIL
        pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Remove background
        output = remove(pil_img, session=self.model)
        
        # Convert back to OpenCV
        result = np.array(output)
        result = cv2.cvtColor(result, cv2.COLOR_RGBA2BGRA)
        
        if return_mask:
            mask = result[:, :, 3]
            return result, mask
        else:
            return result, None
    
    def _remove_with_mediapipe(
        self,
        image: np.ndarray,
        return_mask: bool
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Remove background using MediaPipe."""
        # Convert to RGB
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process
        results = self.model.process(rgb)
        mask = results.segmentation_mask
        
        # Threshold mask
        mask = (mask > 0.5).astype(np.uint8) * 255
        
        # Create RGBA image
        rgba = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = mask
        
        if return_mask:
            return rgba, mask
        else:
            return rgba, None
    
    def refine_mask(
        self,
        mask: np.ndarray,
        feather: int = 5,
        dilate: int = 0,
        erode: int = 0
    ) -> np.ndarray:
        """
        Refine segmentation mask.
        
        Args:
            mask: Input mask
            feather: Edge feathering amount
            dilate: Dilation iterations
            erode: Erosion iterations
        
        Returns:
            Refined mask
        """
        refined = mask.copy()
        
        # Morphological operations
        if erode > 0:
            kernel = np.ones((3, 3), np.uint8)
            refined = cv2.erode(refined, kernel, iterations=erode)
        
        if dilate > 0:
            kernel = np.ones((3, 3), np.uint8)
            refined = cv2.dilate(refined, kernel, iterations=dilate)
        
        # Feather edges
        if feather > 0:
            refined = cv2.GaussianBlur(refined, (feather*2+1, feather*2+1), 0)
        
        return refined


# ═══════════════════════════════════════════════════════════════════════════
# VIRTUAL BACKGROUND GENERATION
# ═══════════════════════════════════════════════════════════════════════════

class VirtualBackgroundGenerator:
    """Generate virtual backgrounds."""
    
    @staticmethod
    def create_gradient_background(
        width: int,
        height: int,
        color1: Tuple[int, int, int] = (26, 26, 46),  # Dark blue
        color2: Tuple[int, int, int] = (73, 73, 120),  # Light blue
        direction: str = "vertical"
    ) -> np.ndarray:
        """
        Create gradient background.
        
        Args:
            width: Width in pixels
            height: Height in pixels
            color1: Start color (BGR)
            color2: End color (BGR)
            direction: Gradient direction (vertical, horizontal, radial)
        
        Returns:
            Background image (BGR)
        """
        bg = np.zeros((height, width, 3), dtype=np.uint8)
        
        if direction == "vertical":
            for i in range(height):
                ratio = i / height
                color = tuple(int(c1 * (1 - ratio) + c2 * ratio) 
                             for c1, c2 in zip(color1, color2))
                bg[i, :] = color
        
        elif direction == "horizontal":
            for j in range(width):
                ratio = j / width
                color = tuple(int(c1 * (1 - ratio) + c2 * ratio)
                             for c1, c2 in zip(color1, color2))
                bg[:, j] = color
        
        elif direction == "radial":
            cy, cx = height // 2, width // 2
            max_dist = np.sqrt(cx**2 + cy**2)
            
            for i in range(height):
                for j in range(width):
                    dist = np.sqrt((j - cx)**2 + (i - cy)**2)
                    ratio = dist / max_dist
                    color = tuple(int(c1 * (1 - ratio) + c2 * ratio)
                                 for c1, c2 in zip(color1, color2))
                    bg[i, j] = color
        
        return bg
    
    @staticmethod
    def create_studio_background(
        width: int,
        height: int,
        style: str = "professional"
    ) -> np.ndarray:
        """
        Create studio-style background.
        
        Args:
            width: Width in pixels
            height: Height in pixels
            style: Style preset (professional, modern, warm, cool)
        
        Returns:
            Background image
        """
        presets = {
            "professional": {
                "color1": (30, 30, 40),
                "color2": (60, 60, 80),
                "direction": "radial"
            },
            "modern": {
                "color1": (20, 30, 40),
                "color2": (40, 60, 80),
                "direction": "vertical"
            },
            "warm": {
                "color1": (30, 40, 60),
                "color2": (60, 80, 120),
                "direction": "radial"
            },
            "cool": {
                "color1": (40, 30, 20),
                "color2": (80, 60, 40),
                "direction": "radial"
            },
            "corporate": {
                "color1": (35, 35, 35),
                "color2": (70, 70, 70),
                "direction": "vertical"
            }
        }
        
        preset = presets.get(style, presets["professional"])
        
        bg = VirtualBackgroundGenerator.create_gradient_background(
            width, height,
            preset["color1"],
            preset["color2"],
            preset["direction"]
        )
        
        # Add subtle texture
        noise = np.random.normal(0, 5, (height, width, 3)).astype(np.int16)
        bg = np.clip(bg.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        return bg
    
    @staticmethod
    def create_bokeh_background(
        width: int,
        height: int,
        num_circles: int = 50,
        color_scheme: str = "warm"
    ) -> np.ndarray:
        """
        Create bokeh light background.
        
        Args:
            width: Width in pixels
            height: Height in pixels
            num_circles: Number of bokeh circles
            color_scheme: Color scheme (warm, cool, multi)
        
        Returns:
            Background image
        """
        # Start with dark background
        bg = np.zeros((height, width, 3), dtype=np.uint8)
        bg[:, :] = (20, 20, 25)
        
        # Color palettes
        palettes = {
            "warm": [(100, 150, 255), (80, 180, 255), (60, 200, 255)],
            "cool": [(255, 200, 100), (255, 180, 80), (255, 150, 60)],
            "multi": [(200, 100, 100), (100, 200, 100), (100, 100, 200), (200, 200, 100)]
        }
        
        colors = palettes.get(color_scheme, palettes["warm"])
        
        # Draw bokeh circles
        for _ in range(num_circles):
            x = np.random.randint(0, width)
            y = np.random.randint(0, height)
            radius = np.random.randint(20, 80)
            color = colors[np.random.randint(0, len(colors))]
            alpha = np.random.uniform(0.3, 0.7)
            
            # Draw circle with transparency
            overlay = bg.copy()
            cv2.circle(overlay, (x, y), radius, color, -1)
            
            # Apply blur
            overlay = cv2.GaussianBlur(overlay, (51, 51), 0)
            
            # Blend
            bg = cv2.addWeighted(bg, 1 - alpha, overlay, alpha, 0)
        
        return bg


# ═══════════════════════════════════════════════════════════════════════════
# DEPTH-BASED BACKGROUND BLUR
# ═══════════════════════════════════════════════════════════════════════════

class DepthEstimator:
    """Estimate depth for realistic background blur."""
    
    def __init__(self):
        self.model = None
    
    def _load_midas(self):
        """Load MiDaS depth estimation model."""
        try:
            import torch
            # Download model if needed
            model_type = "DPT_Small"  # Lighter model
            self.model = torch.hub.load("intel-isl/MiDaS", model_type)
            
            # Use MPS if available, else CPU
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            self.model = self.model.to(device)
            self.model.eval()
            
            # Load transforms
            midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
            self.transform = midas_transforms.small_transform
            
            logger.info(f"✓ MiDaS depth model loaded ({device})")
            return True
        except Exception as e:
            logger.warning(f"MiDaS load failed: {e}")
            return False
    
    def estimate_depth(self, image: np.ndarray) -> np.ndarray:
        """
        Estimate depth map from image.
        
        Args:
            image: Input image (BGR)
        
        Returns:
            Depth map (normalized 0-255)
        """
        if self.model is None:
            if not self._load_midas():
                # Fallback to simple depth estimate
                return self._estimate_depth_simple(image)
        
        try:
            import torch
            
            # Prepare image
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            input_batch = self.transform(rgb)
            
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            input_batch = input_batch.to(device)
            
            # Predict depth
            with torch.no_grad():
                prediction = self.model(input_batch)
                
                prediction = torch.nn.functional.interpolate(
                    prediction.unsqueeze(1),
                    size=image.shape[:2],
                    mode="bicubic",
                    align_corners=False,
                ).squeeze()
            
            depth = prediction.cpu().numpy()
            
            # Normalize to 0-255
            depth = (depth - depth.min()) / (depth.max() - depth.min()) * 255
            depth = depth.astype(np.uint8)
            
            return depth
            
        except Exception as e:
            logger.warning(f"Depth estimation failed: {e}")
            return self._estimate_depth_simple(image)
    
    def _estimate_depth_simple(self, image: np.ndarray) -> np.ndarray:
        """Simple depth estimation fallback."""
        # Use image gradient as rough depth proxy
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)
        depth = np.sqrt(grad_x**2 + grad_y**2)
        depth = (depth / depth.max() * 255).astype(np.uint8)
        return depth


# ═══════════════════════════════════════════════════════════════════════════
# COMPLETE BACKGROUND REPLACEMENT PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def replace_background_video(
    input_video: str,
    output_video: str,
    background: Optional[str] = None,
    background_style: str = "professional",
    blur_background: bool = True,
    blur_amount: int = 15,
    color_match: bool = True,
    edge_refinement: bool = True,
    temp_dir: str = "temp"
) -> str:
    """
    Replace video background with AI segmentation.
    
    Args:
        input_video: Input video path
        output_video: Output video path
        background: Background image/video path (or None for generated)
        background_style: Style if generating background
        blur_background: Blur background for depth effect
        blur_amount: Background blur radius
        color_match: Match subject colors to background
        edge_refinement: Refine edge quality
        temp_dir: Temporary directory
    
    Returns:
        Path to output video
    """
    logger.info(f"Replacing background: {input_video}")
    
    os.makedirs(temp_dir, exist_ok=True)
    
    # Initialize models
    remover = BackgroundRemover(method="rembg")
    
    cap = cv2.VideoCapture(input_video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Prepare background
    if background and os.path.exists(background):
        bg_img = cv2.imread(background)
        if bg_img is None:
            # Video background
            bg_cap = cv2.VideoCapture(background)
        else:
            bg_img = cv2.resize(bg_img, (width, height))
            bg_cap = None
    else:
        # Generate virtual background
        gen = VirtualBackgroundGenerator()
        bg_img = gen.create_studio_background(width, height, style=background_style)
        bg_cap = None
    
    # Blur background if requested
    if blur_background and bg_img is not None:
        bg_img = cv2.GaussianBlur(bg_img, (blur_amount*2+1, blur_amount*2+1), 0)
    
    # Video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_path_temp = os.path.join(temp_dir, "bg_replaced_temp.mp4")
    out = cv2.VideoWriter(out_path_temp, fourcc, fps, (width, height))
    
    frame_idx = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Get current background frame
            if bg_cap is not None:
                ret_bg, current_bg = bg_cap.read()
                if not ret_bg:
                    bg_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret_bg, current_bg = bg_cap.read()
                current_bg = cv2.resize(current_bg, (width, height))
                if blur_background:
                    current_bg = cv2.GaussianBlur(current_bg, (blur_amount*2+1, blur_amount*2+1), 0)
            else:
                current_bg = bg_img.copy()
            
            # Remove background
            rgba, mask = remover.remove_background(frame, return_mask=True)
            
            # Refine mask
            if edge_refinement:
                mask = remover.refine_mask(mask, feather=3, erode=1, dilate=1)
            
            # Extract foreground
            foreground = rgba[:, :, :3]
            alpha = mask / 255.0
            alpha = alpha[:, :, np.newaxis]
            
            # Composite
            result = (foreground * alpha + current_bg * (1 - alpha)).astype(np.uint8)
            
            out.write(result)
            frame_idx += 1
            
            if frame_idx % 50 == 0:
                logger.info(f"Processed {frame_idx}/{total_frames} frames")
    
    finally:
        cap.release()
        if bg_cap:
            bg_cap.release()
        out.release()
    
    # Re-encode with audio
    _reencode_with_audio(out_path_temp, input_video, output_video)
    
    logger.info(f"✓ Background replaced: {output_video}")
    return output_video


def _reencode_with_audio(video_path: str, audio_source: str, output_path: str):
    """Re-encode video with audio from source."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_source,
        "-map", "0:v:0",
        "-map", "1:a:0?",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        logger.warning(f"Re-encode failed: {result.stderr[:300]}")
        import shutil
        shutil.copy2(video_path, output_path)


if __name__ == "__main__":
    # Test background AI
    logger.setLevel(logging.INFO)
    print("Background AI module loaded")
    print("Features: segmentation, virtual backgrounds, depth estimation")
