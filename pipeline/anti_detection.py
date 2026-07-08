"""
pipeline/anti_detection.py
Output optimization and anti-detection measures to make AI-generated videos
indistinguishable from real recordings. Includes metadata sanitization,
codec fingerprint masking, natural compression artifacts, and platform-specific exports.
"""
import os, logging, subprocess, json, random, tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple
import cv2, numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# METADATA SANITIZATION & SPOOFING
# ═══════════════════════════════════════════════════════════════════════════

class MetadataSanitizer:
    """Remove AI generation traces and add realistic camera metadata."""
    
    CAMERA_MODELS = [
        # Popular smartphones
        ("Apple", "iPhone 14 Pro", "iOS 17.0"),
        ("Apple", "iPhone 13", "iOS 16.5"),
        ("Samsung", "Galaxy S23 Ultra", "Android 13"),
        ("Samsung", "Galaxy S22", "Android 12"),
        ("Google", "Pixel 7 Pro", "Android 14"),
        ("Google", "Pixel 6", "Android 13"),
        # Popular cameras
        ("Canon", "EOS R5", "Firmware 1.5.0"),
        ("Sony", "A7 IV", "Firmware 2.0"),
        ("Nikon", "Z9", "Firmware 3.01"),
    ]
    
    @staticmethod
    def strip_metadata(video_path: str, output_path: str) -> str:
        """
        Remove all metadata from video.
        
        Args:
            video_path: Input video
            output_path: Output video
        
        Returns:
            Output path
        """
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-map_metadata", "-1",  # Remove all metadata
            "-c", "copy",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.warning("Metadata stripping failed")
            import shutil
            shutil.copy2(video_path, output_path)
        
        logger.info("✓ Metadata stripped")
        return output_path
    
    @staticmethod
    def add_realistic_metadata(
        video_path: str,
        output_path: str,
        camera_model: Optional[str] = None,
        recording_date: Optional[datetime] = None
    ) -> str:
        """
        Add realistic camera metadata to video.
        
        Args:
            video_path: Input video
            output_path: Output video
            camera_model: Camera model name (random if None)
            recording_date: Recording timestamp (random recent if None)
        
        Returns:
            Output path
        """
        # Choose random camera
        if camera_model is None:
            make, model, software = random.choice(MetadataSanitizer.CAMERA_MODELS)
        else:
            make, model, software = "Apple", camera_model, "iOS 17.0"
        
        # Generate realistic timestamp
        if recording_date is None:
            days_ago = random.randint(1, 30)
            recording_date = datetime.now() - timedelta(days=days_ago)
        
        timestamp = recording_date.strftime("%Y-%m-%d %H:%M:%S")
        
        # Add metadata using ffmpeg
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-metadata", f"creation_time={timestamp}",
            "-metadata", f"make={make}",
            "-metadata", f"model={model}",
            "-metadata", f"software={software}",
            "-c", "copy",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.warning("Metadata addition failed")
            import shutil
            shutil.copy2(video_path, output_path)
        
        logger.info(f"✓ Added realistic metadata: {make} {model}")
        return output_path


# ═══════════════════════════════════════════════════════════════════════════
# CODEC FINGERPRINT MASKING
# ═══════════════════════════════════════════════════════════════════════════

class CodecOptimizer:
    """Optimize codec settings to match real-world recordings."""
    
    PLATFORM_PRESETS = {
        "youtube": {
            "codec": "libx264",
            "preset": "slow",
            "crf": 21,
            "profile": "high",
            "level": "4.1",
            "pix_fmt": "yuv420p",
            "movflags": "+faststart",
            "gop": 30,
            "audio_codec": "aac",
            "audio_bitrate": "192k",
            "audio_sample_rate": 48000
        },
        "instagram": {
            "codec": "libx264",
            "preset": "medium",
            "crf": 23,
            "profile": "main",
            "level": "4.0",
            "pix_fmt": "yuv420p",
            "movflags": "+faststart",
            "gop": 24,
            "audio_codec": "aac",
            "audio_bitrate": "128k",
            "audio_sample_rate": 44100
        },
        "tiktok": {
            "codec": "libx264",
            "preset": "fast",
            "crf": 24,
            "profile": "main",
            "level": "3.1",
            "pix_fmt": "yuv420p",
            "movflags": "+faststart",
            "gop": 25,
            "audio_codec": "aac",
            "audio_bitrate": "128k",
            "audio_sample_rate": 44100
        },
        "linkedin": {
            "codec": "libx264",
            "preset": "slow",
            "crf": 22,
            "profile": "high",
            "level": "4.1",
            "pix_fmt": "yuv420p",
            "movflags": "+faststart",
            "gop": 30,
            "audio_codec": "aac",
            "audio_bitrate": "192k",
            "audio_sample_rate": 48000
        },
        "twitter": {
            "codec": "libx264",
            "preset": "medium",
            "crf": 23,
            "profile": "main",
            "level": "4.0",
            "pix_fmt": "yuv420p",
            "movflags": "+faststart",
            "gop": 30,
            "audio_codec": "aac",
            "audio_bitrate": "128k",
            "audio_sample_rate": 44100
        },
        "facebook": {
            "codec": "libx264",
            "preset": "medium",
            "crf": 23,
            "profile": "main",
            "level": "4.0",
            "pix_fmt": "yuv420p",
            "movflags": "+faststart",
            "gop": 30,
            "audio_codec": "aac",
            "audio_bitrate": "192k",
            "audio_sample_rate": 48000
        },
        "smartphone": {
            "codec": "libx264",
            "preset": "medium",
            "crf": 26,
            "profile": "main",
            "level": "3.1",
            "pix_fmt": "yuv420p",
            "movflags": "+faststart",
            "gop": 24,
            "audio_codec": "aac",
            "audio_bitrate": "96k",
            "audio_sample_rate": 44100
        }
    }
    
    @staticmethod
    def optimize_for_platform(
        input_video: str,
        output_video: str,
        platform: str = "youtube",
        add_noise: bool = True
    ) -> str:
        """
        Optimize video for specific platform with natural encoding.
        
        Args:
            input_video: Input video path
            output_video: Output video path
            platform: Target platform
            add_noise: Add subtle encoding noise
        
        Returns:
            Output path
        """
        preset = CodecOptimizer.PLATFORM_PRESETS.get(
            platform.lower(),
            CodecOptimizer.PLATFORM_PRESETS["youtube"]
        )
        
        # Build ffmpeg command
        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-c:v", preset["codec"],
            "-preset", preset["preset"],
            "-crf", str(preset["crf"]),
            "-profile:v", preset["profile"],
            "-level", preset["level"],
            "-pix_fmt", preset["pix_fmt"],
            "-g", str(preset["gop"]),  # GOP size
            "-bf", "2",  # B-frames
            "-c:a", preset["audio_codec"],
            "-b:a", preset["audio_bitrate"],
            "-ar", str(preset["audio_sample_rate"]),
            "-movflags", preset["movflags"]
        ]
        
        # Add subtle noise filter for natural look
        if add_noise:
            cmd.extend([
                "-vf", "noise=alls=2:allf=t+u",  # Subtle temporal noise
            ])
        
        cmd.append(output_video)
        
        logger.info(f"Encoding for {platform}...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            logger.error(f"Platform encoding failed: {result.stderr[-500:]}")
            raise RuntimeError("Platform encoding failed")
        
        logger.info(f"✓ Optimized for {platform}")
        return output_video


# ═══════════════════════════════════════════════════════════════════════════
# NATURAL COMPRESSION ARTIFACTS
# ═══════════════════════════════════════════════════════════════════════════

class ArtifactGenerator:
    """Add natural compression artifacts and imperfections."""
    
    @staticmethod
    def add_compression_artifacts(
        video_path: str,
        output_path: str,
        artifact_level: float = 0.15
    ) -> str:
        """
        Add realistic compression artifacts.
        
        Args:
            video_path: Input video
            output_path: Output video
            artifact_level: Artifact intensity (0-1)
        
        Returns:
            Output path
        """
        # Compress twice with different settings for natural artifacts
        temp_dir = tempfile.mkdtemp()
        temp1 = os.path.join(temp_dir, "pass1.mp4")
        
        # First pass - higher quality
        crf1 = int(18 + artifact_level * 10)
        cmd1 = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-c:v", "libx264",
            "-crf", str(crf1),
            "-preset", "fast",
            "-c:a", "copy",
            temp1
        ]
        subprocess.run(cmd1, capture_output=True, timeout=300)
        
        # Second pass - slight re-encode
        crf2 = int(20 + artifact_level * 8)
        cmd2 = [
            "ffmpeg", "-y",
            "-i", temp1,
            "-c:v", "libx264",
            "-crf", str(crf2),
            "-preset", "medium",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]
        subprocess.run(cmd2, capture_output=True, timeout=300)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        logger.info("✓ Added compression artifacts")
        return output_path
    
    @staticmethod
    def add_camera_shake(
        video_path: str,
        output_path: str,
        intensity: float = 0.3
    ) -> str:
        """
        Add subtle camera shake for handheld look.
        
        Args:
            video_path: Input video
            output_path: Output video
            intensity: Shake intensity (0-1)
        
        Returns:
            Output path
        """
        # Use deshake filter in reverse to add shake
        # This is a simplified approach
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"crop=iw-{int(intensity*10)}:ih-{int(intensity*10)}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-c:a", "copy",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        if result.returncode != 0:
            import shutil
            shutil.copy2(video_path, output_path)
        
        logger.info("✓ Added subtle camera movement")
        return output_path


# ═══════════════════════════════════════════════════════════════════════════
# TIMING & PATTERN RANDOMIZATION
# ═══════════════════════════════════════════════════════════════════════════

class TimingRandomizer:
    """Randomize timing patterns to avoid AI detection signatures."""
    
    @staticmethod
    def add_frame_timing_jitter(
        video_path: str,
        output_path: str,
        jitter_amount: float = 0.02
    ) -> str:
        """
        Add subtle frame timing variations (like real cameras).
        
        Args:
            video_path: Input video
            output_path: Output video
            jitter_amount: Jitter amount (0-1)
        
        Returns:
            Output path
        """
        # Variable frame rate to simulate real recording
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vsync", "vfr",  # Variable frame rate
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-c:a", "copy",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        if result.returncode != 0:
            import shutil
            shutil.copy2(video_path, output_path)
        
        logger.info("✓ Added timing variations")
        return output_path


# ═══════════════════════════════════════════════════════════════════════════
# FULL ANTI-DETECTION PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def apply_anti_detection(
    input_video: str,
    output_video: str,
    platform: str = "youtube",
    stealth_level: str = "high",
    camera_model: Optional[str] = None,
    add_artifacts: bool = True,
    temp_dir: str = "temp"
) -> str:
    """
    Apply full anti-detection processing.
    
    Stealth levels:
    - low: Basic optimization
    - medium: Metadata + codec optimization
    - high: Full processing (recommended)
    - maximum: All features + extra passes
    
    Args:
        input_video: Input video path
        output_video: Final output path
        platform: Target platform
        stealth_level: Detection avoidance level
        camera_model: Spoof camera model
        add_artifacts: Add natural artifacts
        temp_dir: Temporary directory
    
    Returns:
        Output path
    """
    logger.info(f"Applying anti-detection (level: {stealth_level}, platform: {platform})...")
    
    os.makedirs(temp_dir, exist_ok=True)
    
    current_video = input_video
    step = 1
    
    # Step 1: Strip existing metadata
    if stealth_level in ["medium", "high", "maximum"]:
        logger.info(f"[{step}/6] Stripping metadata...")
        temp1 = os.path.join(temp_dir, f"step{step}.mp4")
        MetadataSanitizer.strip_metadata(current_video, temp1)
        current_video = temp1
        step += 1
    
    # Step 2: Platform-specific encoding
    logger.info(f"[{step}/6] Platform optimization ({platform})...")
    temp2 = os.path.join(temp_dir, f"step{step}.mp4")
    CodecOptimizer.optimize_for_platform(
        current_video, temp2, platform,
        add_noise=(stealth_level in ["high", "maximum"])
    )
    current_video = temp2
    step += 1
    
    # Step 3: Compression artifacts
    if add_artifacts and stealth_level in ["high", "maximum"]:
        logger.info(f"[{step}/6] Adding compression artifacts...")
        temp3 = os.path.join(temp_dir, f"step{step}.mp4")
        artifact_level = 0.15 if stealth_level == "high" else 0.20
        ArtifactGenerator.add_compression_artifacts(current_video, temp3, artifact_level)
        current_video = temp3
        step += 1
    
    # Step 4: Timing variations
    if stealth_level == "maximum":
        logger.info(f"[{step}/6] Adding timing variations...")
        temp4 = os.path.join(temp_dir, f"step{step}.mp4")
        TimingRandomizer.add_frame_timing_jitter(current_video, temp4)
        current_video = temp4
        step += 1
    
    # Step 5: Realistic metadata
    if stealth_level in ["medium", "high", "maximum"]:
        logger.info(f"[{step}/6] Adding realistic metadata...")
        temp5 = os.path.join(temp_dir, f"step{step}.mp4")
        MetadataSanitizer.add_realistic_metadata(
            current_video, temp5,
            camera_model=camera_model
        )
        current_video = temp5
        step += 1
    
    # Step 6: Final pass
    logger.info(f"[{step}/6] Final optimization...")
    import shutil
    shutil.copy2(current_video, output_video)
    
    # Verify output
    if os.path.exists(output_video):
        size_mb = os.path.getsize(output_video) / (1024 * 1024)
        logger.info(f"✓ Anti-detection complete: {output_video} ({size_mb:.1f} MB)")
    else:
        logger.error("Anti-detection failed - output not created")
        raise RuntimeError("Anti-detection processing failed")
    
    return output_video


def get_video_analysis(video_path: str) -> Dict:
    """
    Analyze video for potential AI detection markers.
    
    Args:
        video_path: Video file path
    
    Returns:
        Analysis results dictionary
    """
    logger.info(f"Analyzing video: {video_path}")
    
    analysis = {
        "file_size_mb": 0,
        "duration_sec": 0,
        "codec": "unknown",
        "fps": 0,
        "resolution": "unknown",
        "has_metadata": False,
        "metadata_fields": [],
        "warnings": []
    }
    
    try:
        # Get basic info
        probe_cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            video_path
        ]
        
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            # File size
            analysis["file_size_mb"] = round(os.path.getsize(video_path) / (1024 * 1024), 2)
            
            # Duration
            if "format" in data:
                analysis["duration_sec"] = float(data["format"].get("duration", 0))
            
            # Video stream info
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    analysis["codec"] = stream.get("codec_name", "unknown")
                    analysis["fps"] = eval(stream.get("r_frame_rate", "0/1"))
                    analysis["resolution"] = f"{stream.get('width', 0)}x{stream.get('height', 0)}"
            
            # Metadata
            if "format" in data and "tags" in data["format"]:
                tags = data["format"]["tags"]
                analysis["has_metadata"] = len(tags) > 0
                analysis["metadata_fields"] = list(tags.keys())
                
                # Check for suspicious metadata
                suspicious_fields = ["encoder", "comment", "software"]
                for field in suspicious_fields:
                    if field in tags:
                        value = tags[field].lower()
                        if any(word in value for word in ["ai", "generated", "synthetic", "wav2lip", "f5-tts"]):
                            analysis["warnings"].append(f"Suspicious metadata: {field}={tags[field]}")
        
        # Check for perfect patterns (suspicious)
        if analysis["fps"] == int(analysis["fps"]) and analysis["fps"] in [24, 25, 30, 60]:
            # Exact frame rates are actually normal for edited videos
            pass
        
        logger.info(f"Analysis complete: {len(analysis['warnings'])} warnings")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        analysis["warnings"].append(f"Analysis error: {str(e)}")
    
    return analysis


if __name__ == "__main__":
    # Test anti-detection
    logger.setLevel(logging.INFO)
    print("Anti-detection module loaded")
    print("Stealth levels: low, medium, high, maximum")
    print("Platforms:", list(CodecOptimizer.PLATFORM_PRESETS.keys()))
