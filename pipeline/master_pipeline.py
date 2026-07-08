"""
pipeline/master_pipeline.py
Master pipeline orchestrator that integrates all professional features
into a unified, high-quality video generation system.
"""
import os, sys, logging, time, tempfile, shutil
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from dataclasses import asdict

logger = logging.getLogger(__name__)

# Import all pipeline modules
from pipeline.presets import VideoPreset, PresetLibrary
from pipeline.voice_clone import generate_speech, audio_duration
from pipeline.audio_mastering import master_audio
from pipeline.lip_sync import photo_to_video, run_wav2lip
from pipeline.lip_sync_advanced import run_wav2lip_advanced
from pipeline.natural_motion import add_natural_motion_with_audio
from pipeline.video_enhancement import enhance_video
from pipeline.compositor_advanced import composite_with_realism
from pipeline.background_ai import replace_background_video, VirtualBackgroundGenerator
from pipeline.subtitles_pro import create_professional_subtitles
from pipeline.anti_detection import apply_anti_detection


# ═══════════════════════════════════════════════════════════════════════════
# MASTER PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

class MasterPipeline:
    """Master pipeline for professional AI video generation."""
    
    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        self.start_time = None
        self.checkpoints = {}
    
    def generate_video(
        self,
        script: str,
        avatar_image: str,
        preset: VideoPreset,
        voice_file: Optional[str] = None,
        background_image: Optional[str] = None,
        background_music: Optional[str] = None,
        lower_third_name: str = "",
        lower_third_title: str = "",
        output_path: str = "output.mp4",
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        Generate professional video using all features.
        
        Args:
            script: Text script for narration
            avatar_image: Path to avatar photo
            preset: VideoPreset configuration
            voice_file: Path to voice sample (for cloning)
            background_image: Custom background image/video
            background_music: Background music file
            lower_third_name: Name for lower third
            lower_third_title: Title for lower third
            output_path: Final output path
            progress_callback: Progress callback function(percent, message)
        
        Returns:
            Path to final video
        """
        self.start_time = time.time()
        logger.info(f"Starting master pipeline with preset: {preset.name}")
        
        def update_progress(percent: int, message: str):
            if progress_callback:
                progress_callback(percent, message)
            logger.info(f"[{percent}%] {message}")
        
        try:
            # ──────────────────────────────────────────────────────────────
            # STAGE 1: VOICE GENERATION & AUDIO MASTERING (0-20%)
            # ──────────────────────────────────────────────────────────────
            update_progress(2, "Generating voice narration...")
            
            raw_audio = os.path.join(self.temp_dir, "raw_audio.wav")
            generate_speech(
                script=script,
                reference_audio=voice_file or "",
                output_path=raw_audio,
                speed=preset.voice_speed,
                mode=preset.voice_mode,
                temp_dir=self.temp_dir
            )
            self.checkpoints['raw_audio'] = raw_audio
            
            update_progress(8, "Mastering audio...")
            
            mastered_audio = os.path.join(self.temp_dir, "mastered_audio.wav")
            master_audio(
                input_path=raw_audio,
                output_path=mastered_audio,
                eq_preset=preset.voice_eq_preset,
                add_compression=preset.voice_compression,
                add_reverb=preset.voice_reverb,
                add_deessing=preset.voice_deessing,
                background_music=background_music if preset.background_music else None,
                music_level_db=preset.music_level_db
            )
            self.checkpoints['mastered_audio'] = mastered_audio
            
            audio_dur = audio_duration(mastered_audio)
            update_progress(15, f"Audio ready: {audio_dur:.1f}s")
            
            # ──────────────────────────────────────────────────────────────
            # STAGE 2: BASE VIDEO CREATION (20-35%)
            # ──────────────────────────────────────────────────────────────
            update_progress(20, "Creating base video from avatar...")
            
            base_video = os.path.join(self.temp_dir, "base_video.mp4")
            photo_to_video(
                photo=avatar_image,
                duration=audio_dur,
                out=base_video,
                size=(512, 512)
            )
            self.checkpoints['base_video'] = base_video
            
            # ──────────────────────────────────────────────────────────────
            # STAGE 3: LIP-SYNC (35-60%)
            # ──────────────────────────────────────────────────────────────
            update_progress(35, "Applying advanced lip-sync...")
            
            lipsync_video = os.path.join(self.temp_dir, "lipsync.mp4")
            
            if preset.lipsync_preprocess or preset.lipsync_postprocess:
                # Use advanced lip-sync
                run_wav2lip_advanced(
                    face_video=base_video,
                    audio=mastered_audio,
                    output=lipsync_video,
                    quality=preset.lipsync_quality,
                    temp_dir=self.temp_dir,
                    preprocess=preset.lipsync_preprocess,
                    postprocess=preset.lipsync_postprocess
                )
            else:
                # Use standard lip-sync
                run_wav2lip(
                    face_video=base_video,
                    audio=mastered_audio,
                    out=lipsync_video,
                    quality=preset.lipsync_quality,
                    temp_dir=self.temp_dir
                )
            
            self.checkpoints['lipsync'] = lipsync_video
            update_progress(55, "Lip-sync complete")
            
            # ──────────────────────────────────────────────────────────────
            # STAGE 4: NATURAL MOTION (60-68%)
            # ──────────────────────────────────────────────────────────────
            if preset.head_motion_intensity > 0 or preset.enable_blinks:
                update_progress(60, "Adding natural head movement...")
                
                motion_video = os.path.join(self.temp_dir, "motion.mp4")
                add_natural_motion_with_audio(
                    input_video=lipsync_video,
                    audio_path=mastered_audio,
                    output_video=motion_video,
                    head_motion_intensity=preset.head_motion_intensity,
                    enable_blinks=preset.enable_blinks,
                    enable_breathing=preset.enable_breathing
                )
                lipsync_video = motion_video
                self.checkpoints['motion'] = motion_video
                update_progress(68, "Natural motion added")
            
            # ──────────────────────────────────────────────────────────────
            # STAGE 5: VIDEO ENHANCEMENT (68-75%)
            # ──────────────────────────────────────────────────────────────
            if preset.face_enhancement or preset.denoise:
                update_progress(68, "Enhancing video quality...")
                
                enhanced_video = os.path.join(self.temp_dir, "enhanced.mp4")
                enhance_video(
                    input_path=lipsync_video,
                    output_path=enhanced_video,
                    enhance_face=preset.face_enhancement,
                    face_fidelity=preset.face_fidelity,
                    upscale=preset.upscale_video,
                    upscale_factor=preset.upscale_factor,
                    denoise=preset.denoise,
                    denoise_strength=preset.denoise_strength,
                    color_grade=preset.color_grade,
                    temporal_smooth=preset.temporal_smooth
                )
                lipsync_video = enhanced_video
                self.checkpoints['enhanced'] = enhanced_video
                update_progress(75, "Video enhanced")
            
            # ──────────────────────────────────────────────────────────────
            # STAGE 6: BACKGROUND & COMPOSITING (75-83%)
            # ──────────────────────────────────────────────────────────────
            update_progress(75, "Compositing with background...")
            
            # Prepare background
            if background_image and os.path.exists(background_image):
                bg_path = background_image
            else:
                # Generate virtual background
                gen = VirtualBackgroundGenerator()
                w, h = map(int, preset.resolution.split('x'))
                bg_img = gen.create_studio_background(w, h, preset.background_style)
                bg_path = os.path.join(self.temp_dir, "virtual_bg.jpg")
                import cv2
                cv2.imwrite(bg_path, bg_img)
            
            composited_video = os.path.join(self.temp_dir, "composited.mp4")
            
            # Parse position
            position_map = {
                "center": None,
                "lower_center": None,
                "lower_left": None,
                "lower_right": None,
                "upper_center": None
            }
            
            # Use advanced compositing
            composite_with_realism(
                avatar_path=lipsync_video,
                background_path=bg_path,
                output_path=composited_video,
                scale=preset.avatar_scale,
                add_shadow=preset.add_shadow,
                shadow_intensity=preset.shadow_intensity,
                add_edge_light=preset.add_edge_light,
                edge_light_side=preset.edge_light_side,
                color_match=preset.color_match,
                add_vignette=preset.add_vignette,
                cinematic_grade=(preset.add_film_grain),
                temp_dir=self.temp_dir
            )
            
            self.checkpoints['composited'] = composited_video
            update_progress(83, "Compositing complete")
            
            # ──────────────────────────────────────────────────────────────
            # STAGE 7: SUBTITLES (83-90%)
            # ──────────────────────────────────────────────────────────────
            if preset.subtitles_enabled:
                update_progress(83, "Adding professional subtitles...")
                
                subtitled_video = os.path.join(self.temp_dir, "subtitled.mp4")
                create_professional_subtitles(
                    video_path=composited_video,
                    audio_path=mastered_audio,
                    output_video_path=subtitled_video,
                    style=preset.subtitle_style,
                    use_whisper=preset.use_whisper,
                    whisper_model=preset.whisper_model,
                    words_per_line=preset.words_per_line,
                    temp_dir=self.temp_dir
                )
                composited_video = subtitled_video
                self.checkpoints['subtitled'] = subtitled_video
                update_progress(90, "Subtitles added")
            
            # ──────────────────────────────────────────────────────────────
            # STAGE 8: ANTI-DETECTION & FINAL OPTIMIZATION (90-100%)
            # ──────────────────────────────────────────────────────────────
            update_progress(90, "Applying anti-detection processing...")
            
            apply_anti_detection(
                input_video=composited_video,
                output_video=output_path,
                platform=preset.target_platform,
                stealth_level=preset.anti_detection_level,
                camera_model=preset.camera_model,
                add_artifacts=preset.add_compression_artifacts,
                temp_dir=self.temp_dir
            )
            
            update_progress(98, "Final optimization...")
            
            # ──────────────────────────────────────────────────────────────
            # COMPLETE
            # ──────────────────────────────────────────────────────────────
            elapsed = time.time() - self.start_time
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            
            update_progress(100, f"Complete! ({elapsed/60:.1f}min, {file_size:.1f}MB)")
            
            logger.info(f"✓ Master pipeline complete: {output_path}")
            logger.info(f"  Duration: {audio_dur:.1f}s video in {elapsed/60:.1f}min")
            logger.info(f"  File size: {file_size:.1f}MB")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Master pipeline failed: {e}", exc_info=True)
            raise
        
        finally:
            # Optional: cleanup temp files
            pass
    
    def cleanup(self, keep_checkpoints: bool = False):
        """Clean up temporary files."""
        if not keep_checkpoints:
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                logger.info("✓ Cleaned up temporary files")
            except Exception as e:
                logger.warning(f"Cleanup warning: {e}")


def generate_with_preset(
    script: str,
    avatar_image: str,
    preset_name: str,
    output_path: str,
    **overrides
) -> str:
    """
    Convenient function to generate video with a named preset.
    
    Args:
        script: Text script
        avatar_image: Avatar photo path
        preset_name: Name of preset to use
        output_path: Output video path
        **overrides: Override specific preset settings
    
    Returns:
        Path to generated video
    """
    # Load preset
    preset = PresetLibrary.get_preset(preset_name)
    
    if preset is None:
        raise ValueError(f"Preset not found: {preset_name}")
    
    # Apply overrides
    if overrides:
        preset_dict = asdict(preset)
        preset_dict.update(overrides)
        preset = VideoPreset(**preset_dict)
    
    # Generate
    pipeline = MasterPipeline()
    return pipeline.generate_video(
        script=script,
        avatar_image=avatar_image,
        preset=preset,
        output_path=output_path
    )


if __name__ == "__main__":
    # Test master pipeline
    logging.basicConfig(level=logging.INFO)
    
    print("=== Master Pipeline ===")
    print("Professional AI video generation system")
    print()
    print("Available presets:")
    for preset in PresetLibrary.list_presets():
        print(f"  - {preset.name} ({preset.category})")
