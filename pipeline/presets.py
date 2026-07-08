"""
pipeline/presets.py
Professional presets system for one-click video generation optimized for
different platforms, styles, and use cases. Includes preset management,
configuration templates, and quality tiers.
"""
import json, os, logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# PRESET DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class VideoPreset:
    """Complete video generation preset configuration."""
    
    # Metadata
    name: str
    description: str
    category: str  # platform, style, quality, use_case
    tags: List[str]
    
    # Voice settings
    voice_mode: str = "fast"  # fast, clone
    voice_engine: str = "edge-tts"
    voice_speed: float = 1.0
    voice_eq_preset: str = "broadcast"
    voice_compression: bool = True
    voice_reverb: bool = True
    voice_deessing: bool = True
    background_music: bool = False
    music_level_db: float = -25.0
    
    # Avatar & composition
    avatar_scale: float = 0.55
    avatar_position: str = "lower_center"
    head_motion_intensity: float = 0.8
    enable_blinks: bool = True
    enable_breathing: bool = True
    enable_micro_expressions: bool = False
    
    # Lip sync
    lipsync_quality: str = "enhanced"
    lipsync_preprocess: bool = True
    lipsync_postprocess: bool = True
    lipsync_blend_strength: float = 0.85
    
    # Video enhancement
    face_enhancement: bool = True
    face_fidelity: float = 0.7
    upscale_video: bool = False
    upscale_factor: int = 2
    denoise: bool = True
    denoise_strength: int = 8
    color_grade: str = "natural"
    temporal_smooth: bool = True
    
    # Background & compositing
    background_type: str = "gradient"  # gradient, custom, virtual, remove
    background_style: str = "professional"
    background_blur: bool = False
    background_blur_amount: int = 15
    add_shadow: bool = True
    shadow_intensity: float = 0.6
    add_edge_light: bool = True
    edge_light_side: str = "left"
    color_match: bool = True
    add_vignette: bool = True
    add_film_grain: bool = True
    film_grain_intensity: float = 0.08
    
    # Subtitles
    subtitles_enabled: bool = True
    subtitle_style: str = "professional"
    subtitle_animation: bool = True
    use_whisper: bool = True
    whisper_model: str = "base"
    words_per_line: int = 6
    
    # Output & anti-detection
    resolution: str = "1280x720"
    aspect_ratio: str = "16:9"
    target_platform: str = "youtube"
    anti_detection_level: str = "high"
    add_compression_artifacts: bool = True
    spoof_camera_metadata: bool = True
    camera_model: Optional[str] = None
    
    # Advanced
    enable_advanced_features: bool = True
    processing_priority: str = "quality"  # quality, speed, balanced


# ═══════════════════════════════════════════════════════════════════════════
# BUILT-IN PRESETS
# ═══════════════════════════════════════════════════════════════════════════

class PresetLibrary:
    """Library of professional presets."""
    
    PRESETS = {
        # ─────────────────────────────────────────────────────────────────
        # PLATFORM-SPECIFIC PRESETS
        # ─────────────────────────────────────────────────────────────────
        
        "youtube_professional": VideoPreset(
            name="YouTube Professional",
            description="High-quality preset optimized for YouTube videos. Full quality, professional styling.",
            category="platform",
            tags=["youtube", "professional", "high-quality"],
            
            voice_eq_preset="broadcast",
            voice_compression=True,
            voice_reverb=True,
            
            avatar_scale=0.55,
            avatar_position="lower_center",
            head_motion_intensity=0.8,
            enable_blinks=True,
            enable_breathing=True,
            
            lipsync_quality="enhanced",
            lipsync_preprocess=True,
            lipsync_postprocess=True,
            
            face_enhancement=True,
            denoise=True,
            color_grade="professional",
            
            background_type="gradient",
            background_style="professional",
            add_shadow=True,
            add_edge_light=True,
            add_vignette=True,
            add_film_grain=True,
            
            subtitles_enabled=True,
            subtitle_style="youtube",
            subtitle_animation=True,
            
            resolution="1920x1080",
            aspect_ratio="16:9",
            target_platform="youtube",
            anti_detection_level="high"
        ),
        
        "tiktok_viral": VideoPreset(
            name="TikTok Viral",
            description="Optimized for TikTok with 9:16 format, bold subtitles, and high energy.",
            category="platform",
            tags=["tiktok", "viral", "vertical", "short-form"],
            
            voice_speed=1.05,
            voice_eq_preset="bright",
            
            avatar_scale=0.65,
            avatar_position="center",
            head_motion_intensity=1.0,
            enable_blinks=True,
            
            face_enhancement=True,
            color_grade="vibrant",
            
            background_type="gradient",
            background_style="modern",
            add_shadow=True,
            add_edge_light=True,
            edge_light_side="all",
            
            subtitles_enabled=True,
            subtitle_style="tiktok",
            subtitle_animation=True,
            words_per_line=4,
            
            resolution="1080x1920",
            aspect_ratio="9:16",
            target_platform="tiktok",
            anti_detection_level="high"
        ),
        
        "instagram_reels": VideoPreset(
            name="Instagram Reels",
            description="Perfect for Instagram Reels with 9:16 format and engaging visuals.",
            category="platform",
            tags=["instagram", "reels", "vertical", "social"],
            
            voice_eq_preset="warm",
            
            avatar_scale=0.6,
            avatar_position="center",
            head_motion_intensity=0.9,
            enable_blinks=True,
            enable_breathing=True,
            
            face_enhancement=True,
            color_grade="warm",
            
            background_type="gradient",
            background_style="warm",
            add_shadow=True,
            add_edge_light=True,
            add_vignette=True,
            film_grain_intensity=0.1,
            
            subtitles_enabled=True,
            subtitle_style="instagram",
            subtitle_animation=True,
            
            resolution="1080x1920",
            aspect_ratio="9:16",
            target_platform="instagram",
            anti_detection_level="high"
        ),
        
        "linkedin_professional": VideoPreset(
            name="LinkedIn Professional",
            description="Business-appropriate styling for LinkedIn posts and articles.",
            category="platform",
            tags=["linkedin", "business", "professional", "corporate"],
            
            voice_eq_preset="broadcast",
            voice_compression=True,
            voice_reverb=False,
            
            avatar_scale=0.5,
            avatar_position="lower_center",
            head_motion_intensity=0.5,
            enable_blinks=True,
            
            face_enhancement=True,
            color_grade="natural",
            
            background_type="gradient",
            background_style="corporate",
            add_shadow=True,
            add_edge_light=True,
            add_vignette=False,
            film_grain_intensity=0.05,
            
            subtitles_enabled=True,
            subtitle_style="professional",
            subtitle_animation=False,
            
            resolution="1280x720",
            aspect_ratio="16:9",
            target_platform="linkedin",
            anti_detection_level="high"
        ),
        
        # ─────────────────────────────────────────────────────────────────
        # STYLE PRESETS
        # ─────────────────────────────────────────────────────────────────
        
        "cinematic": VideoPreset(
            name="Cinematic",
            description="Cinematic look with film grain, color grading, and dramatic lighting.",
            category="style",
            tags=["cinematic", "film", "dramatic", "artistic"],
            
            voice_eq_preset="warm",
            voice_reverb=True,
            background_music=True,
            music_level_db=-28.0,
            
            avatar_scale=0.6,
            head_motion_intensity=0.6,
            enable_breathing=True,
            
            face_enhancement=True,
            face_fidelity=0.8,
            color_grade="cinematic",
            
            background_type="gradient",
            background_style="warm",
            add_shadow=True,
            shadow_intensity=0.7,
            add_edge_light=True,
            edge_light_side="left",
            add_vignette=True,
            add_film_grain=True,
            film_grain_intensity=0.15,
            
            subtitles_enabled=True,
            subtitle_style="minimal",
            
            resolution="1920x1080",
            aspect_ratio="16:9",
            anti_detection_level="maximum"
        ),
        
        "documentary": VideoPreset(
            name="Documentary",
            description="Natural, authentic look for educational and documentary content.",
            category="style",
            tags=["documentary", "natural", "authentic", "educational"],
            
            voice_eq_preset="natural",
            voice_compression=False,
            voice_reverb=False,
            
            avatar_scale=0.55,
            head_motion_intensity=0.7,
            enable_blinks=True,
            enable_breathing=True,
            
            face_enhancement=True,
            face_fidelity=0.9,
            color_grade="natural",
            
            background_type="gradient",
            background_style="professional",
            add_shadow=True,
            shadow_intensity=0.5,
            add_edge_light=False,
            add_vignette=False,
            add_film_grain=True,
            film_grain_intensity=0.08,
            
            subtitles_enabled=True,
            subtitle_style="professional",
            
            resolution="1920x1080",
            anti_detection_level="high"
        ),
        
        "podcast_clip": VideoPreset(
            name="Podcast Clip",
            description="Optimized for podcast video clips with clear audio and minimal distractions.",
            category="style",
            tags=["podcast", "audio", "interview", "conversation"],
            
            voice_eq_preset="podcast",
            voice_compression=True,
            voice_reverb=False,
            voice_deessing=True,
            
            avatar_scale=0.5,
            avatar_position="center",
            head_motion_intensity=0.6,
            enable_blinks=True,
            
            face_enhancement=True,
            color_grade="natural",
            
            background_type="gradient",
            background_style="professional",
            add_shadow=True,
            add_edge_light=True,
            add_vignette=True,
            
            subtitles_enabled=True,
            subtitle_style="podcast",
            subtitle_animation=False,
            
            resolution="1920x1080",
            aspect_ratio="16:9",
            anti_detection_level="high"
        ),
        
        # ─────────────────────────────────────────────────────────────────
        # QUALITY PRESETS
        # ─────────────────────────────────────────────────────────────────
        
        "maximum_quality": VideoPreset(
            name="Maximum Quality",
            description="Highest quality settings with all enhancements. Slower processing.",
            category="quality",
            tags=["quality", "premium", "slow", "best"],
            
            voice_eq_preset="broadcast",
            voice_compression=True,
            voice_reverb=True,
            voice_deessing=True,
            
            avatar_scale=0.55,
            head_motion_intensity=0.8,
            enable_blinks=True,
            enable_breathing=True,
            enable_micro_expressions=True,
            
            lipsync_quality="enhanced",
            lipsync_preprocess=True,
            lipsync_postprocess=True,
            lipsync_blend_strength=0.9,
            
            face_enhancement=True,
            face_fidelity=0.9,
            upscale_video=True,
            upscale_factor=2,
            denoise=True,
            denoise_strength=10,
            color_grade="professional",
            temporal_smooth=True,
            
            background_type="gradient",
            add_shadow=True,
            add_edge_light=True,
            color_match=True,
            add_vignette=True,
            add_film_grain=True,
            
            subtitles_enabled=True,
            subtitle_style="professional",
            subtitle_animation=True,
            use_whisper=True,
            whisper_model="medium",
            
            resolution="1920x1080",
            anti_detection_level="maximum",
            processing_priority="quality"
        ),
        
        "fast_preview": VideoPreset(
            name="Fast Preview",
            description="Quick preview with essential features. Fast processing.",
            category="quality",
            tags=["fast", "preview", "draft", "quick"],
            
            voice_mode="fast",
            voice_compression=False,
            voice_reverb=False,
            
            avatar_scale=0.55,
            head_motion_intensity=0.5,
            enable_blinks=False,
            enable_breathing=False,
            
            lipsync_quality="fast",
            lipsync_preprocess=False,
            lipsync_postprocess=False,
            
            face_enhancement=False,
            denoise=False,
            color_grade="natural",
            temporal_smooth=False,
            
            background_type="gradient",
            add_shadow=False,
            add_edge_light=False,
            add_vignette=False,
            add_film_grain=False,
            
            subtitles_enabled=True,
            subtitle_style="minimal",
            subtitle_animation=False,
            use_whisper=False,
            
            resolution="1280x720",
            anti_detection_level="low",
            processing_priority="speed"
        ),
        
        "balanced": VideoPreset(
            name="Balanced",
            description="Good quality with reasonable processing time. Recommended default.",
            category="quality",
            tags=["balanced", "default", "recommended", "moderate"],
            
            voice_eq_preset="broadcast",
            voice_compression=True,
            voice_reverb=True,
            
            avatar_scale=0.55,
            head_motion_intensity=0.8,
            enable_blinks=True,
            enable_breathing=True,
            
            lipsync_quality="enhanced",
            lipsync_preprocess=True,
            lipsync_postprocess=True,
            
            face_enhancement=True,
            face_fidelity=0.7,
            denoise=True,
            denoise_strength=8,
            color_grade="natural",
            
            background_type="gradient",
            add_shadow=True,
            add_edge_light=True,
            add_vignette=True,
            add_film_grain=True,
            film_grain_intensity=0.08,
            
            subtitles_enabled=True,
            subtitle_style="professional",
            subtitle_animation=True,
            use_whisper=True,
            whisper_model="base",
            
            resolution="1280x720",
            anti_detection_level="high",
            processing_priority="balanced"
        ),
        
        # ─────────────────────────────────────────────────────────────────
        # USE CASE PRESETS
        # ─────────────────────────────────────────────────────────────────
        
        "explainer_video": VideoPreset(
            name="Explainer Video",
            description="Clear narration with engaging visuals for tutorials and explanations.",
            category="use_case",
            tags=["explainer", "tutorial", "educational", "how-to"],
            
            voice_eq_preset="broadcast",
            voice_compression=True,
            voice_speed=0.95,
            
            avatar_scale=0.5,
            avatar_position="lower_right",
            head_motion_intensity=0.7,
            
            face_enhancement=True,
            color_grade="natural",
            
            background_type="gradient",
            background_style="professional",
            add_shadow=True,
            add_edge_light=True,
            
            subtitles_enabled=True,
            subtitle_style="youtube",
            subtitle_animation=True,
            words_per_line=8,
            
            resolution="1920x1080",
            aspect_ratio="16:9",
            anti_detection_level="high"
        ),
        
        "product_demo": VideoPreset(
            name="Product Demo",
            description="Professional product demonstration with clear communication.",
            category="use_case",
            tags=["product", "demo", "marketing", "sales"],
            
            voice_eq_preset="professional",
            voice_compression=True,
            
            avatar_scale=0.45,
            avatar_position="lower_left",
            head_motion_intensity=0.6,
            enable_blinks=True,
            
            face_enhancement=True,
            color_grade="professional",
            
            background_type="gradient",
            background_style="corporate",
            add_shadow=True,
            add_edge_light=True,
            add_vignette=True,
            
            subtitles_enabled=True,
            subtitle_style="professional",
            
            resolution="1920x1080",
            anti_detection_level="high"
        ),
        
        "social_media_ad": VideoPreset(
            name="Social Media Ad",
            description="Attention-grabbing format for social media advertising.",
            category="use_case",
            tags=["ad", "advertising", "marketing", "social"],
            
            voice_speed=1.1,
            voice_eq_preset="bright",
            
            avatar_scale=0.65,
            avatar_position="center",
            head_motion_intensity=1.0,
            enable_blinks=True,
            
            face_enhancement=True,
            color_grade="vibrant",
            
            background_type="gradient",
            background_style="modern",
            add_shadow=True,
            add_edge_light=True,
            edge_light_side="all",
            add_vignette=True,
            
            subtitles_enabled=True,
            subtitle_style="tiktok",
            subtitle_animation=True,
            words_per_line=4,
            
            resolution="1080x1080",
            aspect_ratio="1:1",
            anti_detection_level="high"
        ),
        
        "news_report": VideoPreset(
            name="News Report",
            description="Professional news-style presentation with authoritative tone.",
            category="use_case",
            tags=["news", "report", "journalism", "formal"],
            
            voice_eq_preset="broadcast",
            voice_compression=True,
            voice_reverb=False,
            
            avatar_scale=0.5,
            avatar_position="lower_center",
            head_motion_intensity=0.5,
            enable_blinks=True,
            
            face_enhancement=True,
            color_grade="professional",
            
            background_type="gradient",
            background_style="corporate",
            add_shadow=True,
            add_edge_light=True,
            add_vignette=False,
            add_film_grain=True,
            film_grain_intensity=0.05,
            
            subtitles_enabled=True,
            subtitle_style="netflix",
            subtitle_animation=False,
            
            resolution="1920x1080",
            aspect_ratio="16:9",
            anti_detection_level="maximum"
        ),
    }
    
    @classmethod
    def get_preset(cls, name: str) -> Optional[VideoPreset]:
        """Get preset by name."""
        return cls.PRESETS.get(name)
    
    @classmethod
    def list_presets(cls, category: Optional[str] = None) -> List[VideoPreset]:
        """List all presets, optionally filtered by category."""
        presets = list(cls.PRESETS.values())
        if category:
            presets = [p for p in presets if p.category == category]
        return presets
    
    @classmethod
    def list_categories(cls) -> List[str]:
        """List all preset categories."""
        return sorted(set(p.category for p in cls.PRESETS.values()))
    
    @classmethod
    def search_presets(cls, query: str) -> List[VideoPreset]:
        """Search presets by name, description, or tags."""
        query = query.lower()
        results = []
        
        for preset in cls.PRESETS.values():
            if (query in preset.name.lower() or
                query in preset.description.lower() or
                any(query in tag for tag in preset.tags)):
                results.append(preset)
        
        return results


# ═══════════════════════════════════════════════════════════════════════════
# PRESET MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class PresetManager:
    """Manage user presets and preset operations."""
    
    def __init__(self, presets_dir: str = ".kiro/presets"):
        self.presets_dir = Path(presets_dir)
        self.presets_dir.mkdir(parents=True, exist_ok=True)
    
    def save_preset(self, preset: VideoPreset, custom: bool = True) -> bool:
        """
        Save preset to file.
        
        Args:
            preset: Preset to save
            custom: Whether this is a custom user preset
        
        Returns:
            Success status
        """
        try:
            filename = f"{'custom_' if custom else ''}{preset.name.lower().replace(' ', '_')}.json"
            filepath = self.presets_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(asdict(preset), f, indent=2)
            
            logger.info(f"✓ Saved preset: {preset.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save preset: {e}")
            return False
    
    def load_preset(self, name: str) -> Optional[VideoPreset]:
        """Load preset from file."""
        try:
            filename = f"{name.lower().replace(' ', '_')}.json"
            filepath = self.presets_dir / filename
            
            if not filepath.exists():
                # Try custom prefix
                filepath = self.presets_dir / f"custom_{filename}"
            
            if filepath.exists():
                with open(filepath, 'r') as f:
                    data = json.load(f)
                return VideoPreset(**data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load preset: {e}")
            return None
    
    def list_user_presets(self) -> List[str]:
        """List user-created custom presets."""
        custom_presets = []
        
        for file in self.presets_dir.glob("custom_*.json"):
            name = file.stem.replace("custom_", "").replace("_", " ").title()
            custom_presets.append(name)
        
        return sorted(custom_presets)
    
    def delete_preset(self, name: str) -> bool:
        """Delete a user preset."""
        try:
            filename = f"custom_{name.lower().replace(' ', '_')}.json"
            filepath = self.presets_dir / filename
            
            if filepath.exists():
                filepath.unlink()
                logger.info(f"✓ Deleted preset: {name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete preset: {e}")
            return False
    
    def export_preset(self, preset: VideoPreset, export_path: str) -> bool:
        """Export preset to specified path."""
        try:
            with open(export_path, 'w') as f:
                json.dump(asdict(preset), f, indent=2)
            
            logger.info(f"✓ Exported preset to: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export preset: {e}")
            return False
    
    def import_preset(self, import_path: str) -> Optional[VideoPreset]:
        """Import preset from file."""
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)
            
            preset = VideoPreset(**data)
            self.save_preset(preset, custom=True)
            
            logger.info(f"✓ Imported preset: {preset.name}")
            return preset
            
        except Exception as e:
            logger.error(f"Failed to import preset: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════
# PRESET UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def create_custom_preset(
    base_preset_name: str,
    custom_name: str,
    **overrides
) -> VideoPreset:
    """
    Create custom preset by modifying a base preset.
    
    Args:
        base_preset_name: Name of base preset
        custom_name: Name for new preset
        **overrides: Settings to override
    
    Returns:
        New VideoPreset instance
    """
    base = PresetLibrary.get_preset(base_preset_name)
    
    if base is None:
        raise ValueError(f"Base preset not found: {base_preset_name}")
    
    # Convert to dict and apply overrides
    preset_dict = asdict(base)
    preset_dict['name'] = custom_name
    preset_dict['description'] = f"Custom preset based on {base_preset_name}"
    preset_dict['tags'] = ['custom'] + preset_dict.get('tags', [])
    preset_dict.update(overrides)
    
    return VideoPreset(**preset_dict)


def compare_presets(preset1: VideoPreset, preset2: VideoPreset) -> Dict[str, tuple]:
    """
    Compare two presets and return differences.
    
    Returns:
        Dictionary of {field: (preset1_value, preset2_value)}
    """
    dict1 = asdict(preset1)
    dict2 = asdict(preset2)
    
    differences = {}
    
    for key in dict1.keys():
        if dict1[key] != dict2[key]:
            differences[key] = (dict1[key], dict2[key])
    
    return differences


def get_recommended_preset(
    platform: str,
    video_type: str,
    priority: str = "balanced"
) -> str:
    """
    Get recommended preset name based on requirements.
    
    Args:
        platform: Target platform (youtube, tiktok, instagram, etc.)
        video_type: Type of video (tutorial, ad, podcast, etc.)
        priority: Priority (quality, speed, balanced)
    
    Returns:
        Recommended preset name
    """
    recommendations = {
        ("youtube", "tutorial"): "explainer_video",
        ("youtube", "podcast"): "podcast_clip",
        ("youtube", "general"): "youtube_professional",
        ("tiktok", "any"): "tiktok_viral",
        ("instagram", "any"): "instagram_reels",
        ("linkedin", "any"): "linkedin_professional",
        ("facebook", "ad"): "social_media_ad",
        ("twitter", "any"): "social_media_ad",
    }
    
    key = (platform.lower(), video_type.lower())
    preset_name = recommendations.get(key)
    
    if not preset_name:
        key = (platform.lower(), "any")
        preset_name = recommendations.get(key, "balanced")
    
    # Adjust for priority
    if priority == "quality":
        if preset_name in ["balanced", "youtube_professional"]:
            preset_name = "maximum_quality"
    elif priority == "speed":
        preset_name = "fast_preview"
    
    return preset_name


if __name__ == "__main__":
    # Test preset system
    logger.setLevel(logging.INFO)
    
    print("=== Preset Library ===")
    print(f"Total presets: {len(PresetLibrary.PRESETS)}")
    print(f"Categories: {', '.join(PresetLibrary.list_categories())}\n")
    
    print("Platform Presets:")
    for preset in PresetLibrary.list_presets(category="platform"):
        print(f"  - {preset.name}: {preset.description}")
    
    print("\nStyle Presets:")
    for preset in PresetLibrary.list_presets(category="style"):
        print(f"  - {preset.name}: {preset.description}")
    
    print("\nQuality Presets:")
    for preset in PresetLibrary.list_presets(category="quality"):
        print(f"  - {preset.name}: {preset.description}")
    
    print("\nUse Case Presets:")
    for preset in PresetLibrary.list_presets(category="use_case"):
        print(f"  - {preset.name}: {preset.description}")
