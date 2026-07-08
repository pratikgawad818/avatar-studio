"""
pipeline/lip_sync.py
Photo → looped video → Wav2Lip lip-sync → MP4
Compatible with FFmpeg 8.x (no -loop flag)
"""
import os, sys, subprocess, logging
from pathlib import Path

logger = logging.getLogger(__name__)

WAV2LIP_DIR  = Path(__file__).parent.parent / "models" / "Wav2Lip"
CHECKPOINT   = WAV2LIP_DIR / "checkpoints" / "wav2lip_gan.pth"


def _check():
    if not WAV2LIP_DIR.exists():
        raise RuntimeError(
            f"Wav2Lip not found at {WAV2LIP_DIR}.\n"
            "Run: git clone https://github.com/Rudrabha/Wav2Lip.git models/Wav2Lip"
        )
    if not CHECKPOINT.exists():
        raise RuntimeError(
            f"wav2lip_gan.pth not found at {CHECKPOINT}.\n"
            "Download and place in models/Wav2Lip/checkpoints/"
        )


def photo_to_video(photo: str, duration: float, out: str,
                   fps: int = 25, size: tuple = (768, 768)) -> str:  # Higher res base
    """
    Loop a still photo into a silent MP4 of given duration.
    Uses lavfi color source + overlay approach (FFmpeg 8.x compatible).
    """
    w, h = size
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    dur = duration + 0.5

    # FFmpeg 8.x: use color source as base, overlay the image on it
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=black:s={w}x{h}:r={fps}:d={dur}",
        "-i", photo,
        "-filter_complex",
        f"[1:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black[img];"
        f"[0:v][img]overlay=0:0,format=yuv420p",
        "-t", str(dur),
        "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "18", 
        "-profile:v", "high", "-pix_fmt", "yuv420p", out,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"photo_to_video failed:\n{r.stderr[-1500:]}")
    logger.info(f"Base video: {out} ({dur:.1f}s)")
    return out


def _clean_env() -> dict:
    """Return a clean environment safe for Wav2Lip subprocess."""
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "random"
    return env


def run_wav2lip(face_video: str, audio: str, out: str,
                quality: str = "enhanced", temp_dir: str = "temp",
                batch_size: int = 128) -> str:
    """Run Wav2Lip inference, returns path to lip-synced MP4."""
    _check()
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    avi_out = os.path.join(temp_dir, "wav2lip_raw.avi")

    if sys.path[0] != str(WAV2LIP_DIR):
        sys.path.insert(0, str(WAV2LIP_DIR))

    ckpt = str(CHECKPOINT)
    if quality == "fast":
        fast = CHECKPOINT.parent / "wav2lip.pth"
        if fast.exists():
            ckpt = str(fast)

    cmd = [
        sys.executable,
        str(WAV2LIP_DIR / "inference.py"),
        "--checkpoint_path", ckpt,
        "--face", face_video,
        "--audio", audio,
        "--outfile", avi_out,
        "--fps", "25",
        "--pads", "0", "10", "0", "0",
        "--wav2lip_batch_size", str(batch_size),
        "--resize_factor", "1",
    ]
    logger.info(f"Wav2Lip starting (batch={batch_size})...")
    r = subprocess.run(cmd, capture_output=True, text=True,
                       cwd=str(WAV2LIP_DIR), env=_clean_env(), timeout=900)
    if r.returncode != 0:
        raise RuntimeError(f"Wav2Lip failed:\n{r.stderr[-2000:]}")

    # AVI → MP4 with higher quality
    cmd2 = ["ffmpeg", "-y", "-i", avi_out,
            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", out]
    subprocess.run(cmd2, check=True, capture_output=True, timeout=60)
    logger.info(f"Lip-sync done: {out}")
    return out
