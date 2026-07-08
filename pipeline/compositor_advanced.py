"""
pipeline/compositor_advanced.py
Advanced compositing with realistic shadows, edge lighting, depth of field,
color matching, reflection effects, and cinematic vignettes.
"""
import os, logging, subprocess, cv2, numpy as np
from pathlib import Path
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# SHADOW GENERATION
# ═══════════════════════════════════════════════════════════════════════════

class ShadowGenerator:
    """Generate realistic dynamic shadows for avatars."""
    
    @staticmethod
    def create_drop_shadow(
        mask: np.ndarray,
        intensity: float = 0.6,
        blur_radius: int = 15,
        offset_x: int = 10,
        offset_y: int = 15,
        softness: float = 0.8
    ) -> np.ndarray:
        """
        Create a realistic drop shadow from an alpha mask.
        
        Args:
            mask: Alpha mask of the subject (0-255)
            intensity: Shadow darkness (0-1)
            blur_radius: Shadow blur amount
            offset_x: Horizontal shadow offset
            offset_y: Vertical shadow offset
            softness: Shadow edge softness
        
        Returns:
            Shadow layer (grayscale)
        """
        # Create shadow canvas
        h, w = mask.shape[:2]
        shadow = np.zeros((h, w), dtype=np.uint8)
        
        # Shift mask to create shadow position
        if offset_y >= 0 and offset_x >= 0:
            shadow[offset_y:, offset_x:] = mask[:h-offset_y, :w-offset_x]
        elif offset_y >= 0 and offset_x < 0:
            shadow[offset_y:, :w+offset_x] = mask[:h-offset_y, -offset_x:]
        elif offset_y < 0 and offset_x >= 0:
            shadow[:h+offset_y, offset_x:] = mask[-offset_y:, :w-offset_x]
        else:
            shadow[:h+offset_y, :w+offset_x] = mask[-offset_y:, -offset_x:]
        
        # Blur for soft edges
        shadow = cv2.GaussianBlur(shadow, (blur_radius*2+1, blur_radius*2+1), 0)
        
        # Apply intensity and softness
        shadow = (shadow * intensity * softness).astype(np.uint8)
        
        return shadow
    
    @staticmethod
    def create_contact_shadow(
        mask: np.ndarray,
        ground_y: int,
        intensity: float = 0.5,
        falloff: float = 0.7
    ) -> np.ndarray:
        """
        Create contact shadow at ground level.
        
        Args:
            mask: Alpha mask
            ground_y: Y position of ground plane
            intensity: Shadow intensity
            falloff: Shadow falloff rate
        
        Returns:
            Contact shadow layer
        """
        h, w = mask.shape[:2]
        shadow = np.zeros((h, w), dtype=np.float32)
        
        # Find bottom of mask
        mask_binary = (mask > 10).astype(np.uint8)
        
        for x in range(w):
            column = mask_binary[:, x]
            if column.any():
                bottom = np.where(column)[0][-1]
                
                # Create gradient from bottom to ground
                if bottom < ground_y:
                    for y in range(bottom, min(ground_y + 50, h)):
                        distance = y - bottom
                        shadow_val = intensity * np.exp(-distance * falloff / 20)
                        shadow[y, max(0, x-10):min(w, x+10)] += shadow_val
        
        shadow = np.clip(shadow * 255, 0, 255).astype(np.uint8)
        return shadow
    
    @staticmethod
    def apply_shadow_to_background(
        background: np.ndarray,
        shadow: np.ndarray,
        blend_mode: str = "multiply"
    ) -> np.ndarray:
        """
        Composite shadow onto background.
        
        Args:
            background: Background image (BGR)
            shadow: Shadow layer (grayscale)
            blend_mode: Blending mode (multiply, normal)
        
        Returns:
            Background with shadow
        """
        if shadow.ndim == 2:
            shadow = shadow[:, :, np.newaxis]
        
        shadow_norm = shadow / 255.0
        
        if blend_mode == "multiply":
            # Darken background where shadow exists
            result = (background * (1 - shadow_norm * 0.7)).astype(np.uint8)
        else:  # normal
            darkened = (background * 0.3).astype(np.uint8)
            result = (background * (1 - shadow_norm) + darkened * shadow_norm).astype(np.uint8)
        
        return result


# ═══════════════════════════════════════════════════════════════════════════
# EDGE LIGHTING (RIM LIGHTING)
# ═══════════════════════════════════════════════════════════════════════════

class EdgeLighting:
    """Add realistic edge/rim lighting to subjects."""
    
    @staticmethod
    def create_edge_light(
        image: np.ndarray,
        mask: np.ndarray,
        light_color: Tuple[int, int, int] = (255, 255, 230),  # Warm white
        intensity: float = 0.4,
        thickness: int = 3,
        side: str = "left"  # left, right, top, all
    ) -> np.ndarray:
        """
        Add edge lighting effect.
        
        Args:
            image: Input image (BGR)
            mask: Alpha mask
            light_color: RGB light color
            intensity: Light intensity (0-1)
            thickness: Edge thickness in pixels
            side: Which side to light (left, right, top, all)
        
        Returns:
            Image with edge lighting
        """
        # Detect edges
        edges = cv2.Canny(mask, 50, 150)
        
        # Dilate to create thickness
        kernel = np.ones((thickness, thickness), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Create directional mask based on side
        h, w = mask.shape
        direction_mask = np.zeros_like(edges, dtype=np.float32)
        
        if side == "left" or side == "all":
            # Gradient from left
            for x in range(w):
                direction_mask[:, x] = max(0, 1 - x / (w * 0.3))
        
        if side == "right" or side == "all":
            # Gradient from right
            for x in range(w):
                direction_mask[:, x] = max(direction_mask[:, x], 1 - (w - x) / (w * 0.3))
        
        if side == "top" or side == "all":
            # Gradient from top
            for y in range(h):
                direction_mask[y, :] = np.maximum(direction_mask[y, :], 1 - y / (h * 0.3))
        
        # Apply direction mask to edges
        light_mask = (edges / 255.0) * direction_mask * intensity
        light_mask = np.clip(light_mask, 0, 1)
        
        # Create colored light
        light_layer = np.zeros_like(image, dtype=np.float32)
        for i, c in enumerate([light_color[2], light_color[1], light_color[0]]):  # BGR
            light_layer[:, :, i] = light_mask * c
        
        # Blend with screen mode
        result = image.astype(np.float32)
        result = result + light_layer * (1 - result / 255.0)
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        logger.info(f"Applied {side} edge lighting")
        return result


# ═══════════════════════════════════════════════════════════════════════════
# DEPTH OF FIELD (BOKEH)
# ═══════════════════════════════════════════════════════════════════════════

class DepthOfField:
    """Create depth of field effect with foreground/background blur."""
    
    @staticmethod
    def create_depth_map(
        image_shape: Tuple[int, int],
        subject_bbox: Tuple[int, int, int, int],  # x, y, w, h
        focus_distance: float = 0.5
    ) -> np.ndarray:
        """
        Create a depth map (0=near, 1=far).
        
        Args:
            image_shape: (height, width)
            subject_bbox: Bounding box of focused subject
            focus_distance: Focus plane distance (0-1)
        
        Returns:
            Depth map (float, 0-1)
        """
        h, w = image_shape
        x, y, bw, bh = subject_bbox
        
        # Create distance map from subject
        depth_map = np.ones((h, w), dtype=np.float32)
        
        # Subject is in focus
        center_x = x + bw // 2
        center_y = y + bh // 2
        
        for i in range(h):
            for j in range(w):
                # Distance from subject center
                dx = (j - center_x) / w
                dy = (i - center_y) / h
                distance = np.sqrt(dx**2 + dy**2)
                
                # Map to depth (subject = focus_distance)
                depth_map[i, j] = focus_distance + distance * 0.5
        
        depth_map = np.clip(depth_map, 0, 1)
        return depth_map
    
    @staticmethod
    def apply_dof(
        image: np.ndarray,
        depth_map: np.ndarray,
        focus_depth: float = 0.5,
        blur_amount: int = 15,
        aperture: float = 2.8
    ) -> np.ndarray:
        """
        Apply depth of field blur.
        
        Args:
            image: Input image
            depth_map: Depth map (0-1)
            focus_depth: Depth value in focus
            blur_amount: Maximum blur radius
            aperture: Simulated aperture (lower = more blur)
        
        Returns:
            Image with DOF
        """
        # Calculate blur amount for each pixel based on distance from focus
        blur_map = np.abs(depth_map - focus_depth) * blur_amount
        blur_map = blur_map.astype(np.uint8)
        
        # Apply variable blur (simplified - real DOF is more complex)
        result = image.copy()
        
        # Blur in stages for efficiency
        for blur_level in [3, 7, 11, 15]:
            mask = (blur_map >= blur_level).astype(np.uint8) * 255
            if mask.any():
                blurred = cv2.GaussianBlur(image, (blur_level*2+1, blur_level*2+1), 0)
                mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
                result = (result * (1 - mask_3ch) + blurred * mask_3ch).astype(np.uint8)
        
        logger.info("Applied depth of field")
        return result


# ═══════════════════════════════════════════════════════════════════════════
# COLOR MATCHING & GRADING
# ═══════════════════════════════════════════════════════════════════════════

class ColorMatcher:
    """Match avatar colors to background environment."""
    
    @staticmethod
    def match_color_temperature(
        subject: np.ndarray,
        background: np.ndarray,
        strength: float = 0.5
    ) -> np.ndarray:
        """
        Match subject color temperature to background.
        
        Args:
            subject: Subject image
            background: Background image
            strength: Matching strength (0-1)
        
        Returns:
            Color-matched subject
        """
        # Convert to LAB color space
        subject_lab = cv2.cvtColor(subject, cv2.COLOR_BGR2LAB).astype(np.float32)
        bg_lab = cv2.cvtColor(background, cv2.COLOR_BGR2LAB).astype(np.float32)
        
        # Calculate average color temperature (a and b channels)
        bg_a_mean = bg_lab[:, :, 1].mean()
        bg_b_mean = bg_lab[:, :, 2].mean()
        
        subj_a_mean = subject_lab[:, :, 1].mean()
        subj_b_mean = subject_lab[:, :, 2].mean()
        
        # Adjust subject towards background
        subject_lab[:, :, 1] += (bg_a_mean - subj_a_mean) * strength
        subject_lab[:, :, 2] += (bg_b_mean - subj_b_mean) * strength
        
        subject_lab = np.clip(subject_lab, 0, 255).astype(np.uint8)
        result = cv2.cvtColor(subject_lab, cv2.COLOR_LAB2BGR)
        
        logger.info("Applied color temperature matching")
        return result
    
    @staticmethod
    def match_luminance(
        subject: np.ndarray,
        background: np.ndarray,
        strength: float = 0.3
    ) -> np.ndarray:
        """
        Match subject luminance to background.
        
        Args:
            subject: Subject image
            background: Background image
            strength: Matching strength (0-1)
        
        Returns:
            Luminance-matched subject
        """
        # Convert to LAB
        subject_lab = cv2.cvtColor(subject, cv2.COLOR_BGR2LAB).astype(np.float32)
        bg_lab = cv2.cvtColor(background, cv2.COLOR_BGR2LAB).astype(np.float32)
        
        # Calculate luminance ratio
        bg_l_mean = bg_lab[:, :, 0].mean()
        subj_l_mean = subject_lab[:, :, 0].mean()
        
        # Adjust subject luminance
        ratio = bg_l_mean / (subj_l_mean + 1e-6)
        adjustment = 1 + (ratio - 1) * strength
        
        subject_lab[:, :, 0] *= adjustment
        subject_lab[:, :, 0] = np.clip(subject_lab[:, :, 0], 0, 255)
        
        result = cv2.cvtColor(subject_lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
        
        logger.info("Applied luminance matching")
        return result


# ═══════════════════════════════════════════════════════════════════════════
# VIGNETTE & ATMOSPHERIC EFFECTS
# ═══════════════════════════════════════════════════════════════════════════

class AtmosphericEffects:
    """Add cinematic atmospheric effects."""
    
    @staticmethod
    def create_vignette(
        image: np.ndarray,
        intensity: float = 0.5,
        radius: float = 0.7
    ) -> np.ndarray:
        """
        Create professional vignette effect.
        
        Args:
            image: Input image
            intensity: Vignette intensity (0-1)
            radius: Vignette radius (0-1, larger = softer)
        
        Returns:
            Image with vignette
        """
        h, w = image.shape[:2]
        
        # Create radial gradient
        y, x = np.ogrid[:h, :w]
        cx, cy = w / 2, h / 2
        
        # Distance from center (normalized)
        distance = np.sqrt((x - cx)**2 + (y - cy)**2)
        max_dist = np.sqrt(cx**2 + cy**2)
        distance = distance / max_dist
        
        # Create vignette mask (smooth falloff)
        vignette = 1 - np.clip((distance - radius) / (1 - radius), 0, 1) ** 2
        vignette = 1 - (1 - vignette) * intensity
        vignette = vignette[:, :, np.newaxis]
        
        # Apply to image
        result = (image * vignette).astype(np.uint8)
        
        return result
    
    @staticmethod
    def add_film_grain(
        image: np.ndarray,
        intensity: float = 0.15,
        grain_size: float = 1.0
    ) -> np.ndarray:
        """
        Add subtle film grain for organic look.
        
        Args:
            image: Input image
            intensity: Grain intensity (0-1)
            grain_size: Grain particle size
        
        Returns:
            Image with grain
        """
        h, w = image.shape[:2]
        
        # Generate noise
        noise = np.random.normal(0, intensity * 25, (h, w, 3))
        
        # Scale noise if grain_size != 1
        if grain_size != 1.0:
            scale = int(max(1, 1 / grain_size))
            small_h, small_w = h // scale, w // scale
            noise_small = cv2.resize(noise, (small_w, small_h))
            noise = cv2.resize(noise_small, (w, h), interpolation=cv2.INTER_LINEAR)
        
        # Add noise to image
        result = image.astype(np.float32) + noise
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return result
    
    @staticmethod
    def add_chromatic_aberration(
        image: np.ndarray,
        amount: int = 2
    ) -> np.ndarray:
        """
        Add subtle chromatic aberration for lens realism.
        
        Args:
            image: Input image
            amount: Aberration amount in pixels
        
        Returns:
            Image with chromatic aberration
        """
        b, g, r = cv2.split(image)
        
        # Shift red channel slightly
        M = np.float32([[1, 0, amount], [0, 1, 0]])
        r = cv2.warpAffine(r, M, (image.shape[1], image.shape[0]))
        
        # Shift blue channel opposite direction
        M = np.float32([[1, 0, -amount], [0, 1, 0]])
        b = cv2.warpAffine(b, M, (image.shape[1], image.shape[0]))
        
        result = cv2.merge([b, g, r])
        return result


# ═══════════════════════════════════════════════════════════════════════════
# ADVANCED COMPOSITING PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def composite_with_realism(
    avatar_path: str,
    background_path: str,
    output_path: str,
    position: Tuple[int, int] = None,  # (x, y) center position
    scale: float = 0.55,
    add_shadow: bool = True,
    shadow_intensity: float = 0.6,
    add_edge_light: bool = True,
    edge_light_side: str = "left",
    color_match: bool = True,
    add_dof: bool = False,
    add_vignette: bool = True,
    cinematic_grade: bool = True,
    temp_dir: str = "temp"
) -> str:
    """
    Composite avatar onto background with professional realism.
    
    Args:
        avatar_path: Path to avatar video
        background_path: Path to background image/video
        output_path: Output video path
        position: Avatar center position
        scale: Avatar scale
        add_shadow: Add realistic shadow
        shadow_intensity: Shadow darkness
        add_edge_light: Add rim lighting
        edge_light_side: Light direction
        color_match: Match colors to background
        add_dof: Add depth of field
        add_vignette: Add cinematic vignette
        cinematic_grade: Apply cinematic color grade
        temp_dir: Temporary directory
    
    Returns:
        Path to composited video
    """
    logger.info("Advanced compositing with realism...")
    
    os.makedirs(temp_dir, exist_ok=True)
    
    # This is a frame-by-frame processing example
    # For full implementation, process video with cv2.VideoCapture/VideoWriter
    
    cap = cv2.VideoCapture(avatar_path)
    bg_img = cv2.imread(background_path)
    
    if bg_img is None:
        # Background is video
        bg_cap = cv2.VideoCapture(background_path)
        ret, bg_img = bg_cap.read()
        bg_cap.release()
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Get dimensions
    ret, first_frame = cap.read()
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    if not ret:
        logger.error("Cannot read avatar video")
        return avatar_path
    
    # Output dimensions
    out_h, out_w = bg_img.shape[:2]
    
    # Video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_writer = cv2.VideoWriter(
        os.path.join(temp_dir, "composited_temp.mp4"),
        fourcc, fps, (out_w, out_h)
    )
    
    # Process frames
    shadow_gen = ShadowGenerator()
    edge_light = EdgeLighting()
    color_matcher = ColorMatcher()
    atmosphere = AtmosphericEffects()
    
    frame_idx = 0
    
    try:
        while True:
            ret, avatar_frame = cap.read()
            if not ret:
                break
            
            # Resize avatar
            ah, aw = avatar_frame.shape[:2]
            new_w = int(out_w * scale)
            new_h = int(new_w * ah / aw)
            avatar_resized = cv2.resize(avatar_frame, (new_w, new_h))
            
            # Position avatar
            if position is None:
                # Center bottom
                pos_x = (out_w - new_w) // 2
                pos_y = out_h - new_h - 50
            else:
                pos_x = position[0] - new_w // 2
                pos_y = position[1] - new_h // 2
            
            # Create mask (assume white/light background on avatar)
            gray = cv2.cvtColor(avatar_resized, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
            
            # Start with background
            composite = bg_img.copy()
            
            # Add shadow
            if add_shadow:
                shadow = shadow_gen.create_drop_shadow(
                    mask, intensity=shadow_intensity,
                    offset_x=10, offset_y=15
                )
                
                # Create shadow canvas
                shadow_canvas = np.zeros_like(composite[:, :, 0])
                y1, y2 = pos_y, min(pos_y + new_h, out_h)
                x1, x2 = pos_x, min(pos_x + new_w, out_w)
                
                shadow_canvas[y1:y2, x1:x2] = shadow[:y2-y1, :x2-x1]
                composite = shadow_gen.apply_shadow_to_background(composite, shadow_canvas)
            
            # Color matching
            if color_match:
                avatar_resized = color_matcher.match_color_temperature(avatar_resized, bg_img, strength=0.4)
                avatar_resized = color_matcher.match_luminance(avatar_resized, bg_img, strength=0.3)
            
            # Edge lighting
            if add_edge_light:
                avatar_resized = edge_light.create_edge_light(
                    avatar_resized, mask,
                    intensity=0.4, side=edge_light_side
                )
            
            # Composite avatar
            mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
            
            y1, y2 = pos_y, min(pos_y + new_h, out_h)
            x1, x2 = pos_x, min(pos_x + new_w, out_w)
            
            if y1 >= 0 and x1 >= 0:
                roi = composite[y1:y2, x1:x2]
                blended = (avatar_resized[:y2-y1, :x2-x1] * mask_3ch[:y2-y1, :x2-x1] +
                          roi * (1 - mask_3ch[:y2-y1, :x2-x1]))
                composite[y1:y2, x1:x2] = blended.astype(np.uint8)
            
            # Atmospheric effects
            if add_vignette:
                composite = atmosphere.create_vignette(composite, intensity=0.4)
            
            if cinematic_grade:
                # Subtle film grain
                composite = atmosphere.add_film_grain(composite, intensity=0.08)
            
            out_writer.write(composite)
            frame_idx += 1
            
            if frame_idx % 50 == 0:
                logger.info(f"Composited {frame_idx}/{frame_count} frames")
    
    finally:
        cap.release()
        out_writer.release()
    
    # Re-encode with audio using ffmpeg
    temp_video = os.path.join(temp_dir, "composited_temp.mp4")
    _reencode_with_audio(temp_video, avatar_path, output_path)
    
    logger.info(f"✓ Advanced composite complete: {output_path}")
    return output_path


def _reencode_with_audio(video_path: str, audio_source: str, output_path: str):
    """Re-encode video with audio from source."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_source,
        "-map", "0:v:0",
        "-map", "1:a:0?",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        logger.warning(f"Re-encode failed: {result.stderr[:500]}")
        import shutil
        shutil.copy2(video_path, output_path)


if __name__ == "__main__":
    # Test advanced compositing
    logger.setLevel(logging.INFO)
    print("Advanced compositor loaded")
    print("Features: shadows, edge lighting, color matching, DOF, vignette, film grain")
