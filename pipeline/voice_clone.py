"""
pipeline/voice_clone.py
Two-engine voice system:
  - FAST mode (default): edge-tts — instant, no GPU, great quality, many voices
  - CLONE mode: F5-TTS on MPS — uses your voice sample, slower (~2-5 min)
"""
import os, sys, shutil, subprocess, logging, tempfile, re, time, asyncio
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

VENV_PYTHON = Path(__file__).parent.parent / "venv" / "bin" / "python3"


class VoiceCloneError(Exception):
    pass


def estimate_generation_time(word_count: int, mode: str = "fast") -> int:
    """Estimate seconds. Fast mode = instant, clone = slow."""
    if mode == "fast":
        return max(5, int(word_count * 0.3))  # edge-tts is near instant
    return max(60, int(word_count * 4))  # F5-TTS on MPS


def audio_duration(path: str) -> float:
    if not os.path.exists(path):
        return 0.0
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=10
        )
        return float(r.stdout.strip()) if r.returncode == 0 else 0.0
    except (ValueError, subprocess.TimeoutExpired):
        return 0.0


def normalize_audio(src: str, dst: str, sr: int = 22050, channels: int = 1):
    if not os.path.exists(src):
        raise VoiceCloneError(f"Audio not found: {src}")
    cmd = ["ffmpeg", "-y", "-i", src,
           "-ac", str(channels), "-ar", str(sr), "-acodec", "pcm_s16le", dst]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise VoiceCloneError(f"Audio conversion failed")


def to_wav2lip_audio(src: str, dst: str):
    normalize_audio(src, dst, sr=16000, channels=1)


# ══════════════════════════════════════════════════════════════════════════════
# FAST ENGINE: edge-tts (default)
# ══════════════════════════════════════════════════════════════════════════════

# Good voices for edge-tts
EDGE_VOICES = {
    "male_us":    "en-US-GuyNeural",
    "female_us":  "en-US-JennyNeural",
    "male_uk":    "en-GB-RyanNeural",
    "female_uk":  "en-GB-SoniaNeural",
    "male_au":    "en-AU-WilliamNeural",
    "female_au":  "en-AU-NatashaNeural",
    "male_in":    "en-IN-PrabhatNeural",
    "female_in":  "en-IN-NeerjaNeural",
}

_EDGE_SCRIPT = """
import sys, asyncio, edge_tts

text    = sys.argv[1]
voice   = sys.argv[2]
output  = sys.argv[3]
rate    = sys.argv[4]

async def main():
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output)
    print("EDGE_DONE:" + output)

asyncio.run(main())
"""


def generate_speech_fast(
    script: str,
    output_path: str,
    voice: str = "en-US-GuyNeural",
    speed: float = 1.0,
    temp_dir: str = "temp",
) -> str:
    """Generate speech using edge-tts — instant, no local compute."""
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Convert speed to edge-tts rate format (e.g. +10%, -20%)
    rate_pct = int((speed - 1.0) * 100)
    rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

    mp3_out = os.path.join(temp_dir, "edge_raw.mp3")
    python = str(VENV_PYTHON)

    logger.info(f"edge-tts: generating with voice={voice}, rate={rate_str}")
    t0 = time.time()

    r = subprocess.run(
        [python, "-c", _EDGE_SCRIPT, script, voice, mp3_out, rate_str],
        capture_output=True, text=True, timeout=60,
    )

    if r.returncode != 0:
        logger.error(f"edge-tts failed: {r.stderr[-500:]}")
        raise VoiceCloneError(f"edge-tts failed: {r.stderr[-300:]}")

    if "EDGE_DONE" not in r.stdout:
        raise VoiceCloneError("edge-tts did not complete")

    elapsed = time.time() - t0
    logger.info(f"✓ edge-tts done in {elapsed:.1f}s")

    # Convert MP3 → WAV for Wav2Lip
    to_wav2lip_audio(mp3_out, output_path)

    dur = audio_duration(output_path)
    logger.info(f"✓ Speech: {dur:.1f}s ({len(script.split())} words in {elapsed:.1f}s)")
    return output_path


# ══════════════════════════════════════════════════════════════════════════════
# CLONE ENGINE: F5-TTS (optional, slower)
# ══════════════════════════════════════════════════════════════════════════════

_F5_SCRIPT = """
import sys, os, time
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

ref_audio   = sys.argv[1]
ref_text    = sys.argv[2]
gen_text    = sys.argv[3]
output_file = sys.argv[4]
speed       = float(sys.argv[5])

import torch
from f5_tts.api import F5TTS

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"F5TTS_STATUS:device:{device}", flush=True)

t0 = time.time()
tts = F5TTS(device=device)
print(f"F5TTS_STATUS:model_loaded:{time.time()-t0:.1f}s", flush=True)

t1 = time.time()
tts.infer(
    ref_file  = ref_audio,
    ref_text  = ref_text,
    gen_text  = gen_text,
    speed     = speed,
    file_wave = output_file,
)
print(f"F5TTS_STATUS:done:{time.time()-t1:.1f}s", flush=True)
print("F5TTS_DONE:" + output_file)
"""


def generate_speech_clone(
    script: str,
    reference_audio: str,
    output_path: str,
    reference_text: str = "",
    speed: float = 1.0,
    temp_dir: str = "temp",
) -> str:
    """Generate speech using F5-TTS voice cloning (MPS). Slower but clones your voice."""
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Normalize + trim reference
    ref_clean = os.path.join(temp_dir, "ref_clean.wav")
    normalize_audio(reference_audio, ref_clean, sr=22050)

    # Trim to 10s for speed
    ref_dur = audio_duration(ref_clean)
    if ref_dur > 10:
        trimmed = os.path.join(temp_dir, "ref_trimmed.wav")
        subprocess.run(
            ["ffmpeg", "-y", "-i", ref_clean, "-t", "10",
             "-ac", "1", "-ar", "22050", "-acodec", "pcm_s16le", trimmed],
            capture_output=True, timeout=15
        )
        ref_clean = trimmed
        logger.info(f"Trimmed reference from {ref_dur:.0f}s to 10s")

    raw_out = os.path.join(temp_dir, "raw_speech.wav")
    python = str(VENV_PYTHON)
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "random"
    env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

    word_count = len(script.split())
    logger.info(f"F5-TTS (MPS): {word_count} words, ref={audio_duration(ref_clean):.1f}s")

    t0 = time.time()
    try:
        r = subprocess.run(
            [python, "-c", _F5_SCRIPT,
             ref_clean, reference_text, script, raw_out, str(speed)],
            capture_output=True, text=True,
            env=env, timeout=600,
        )
    except subprocess.TimeoutExpired:
        raise VoiceCloneError("F5-TTS timed out (10 min). Try a shorter script.")

    elapsed = time.time() - t0

    if r.returncode != 0:
        logger.error(f"F5-TTS failed ({elapsed:.0f}s): {r.stderr[-1000:]}")
        raise VoiceCloneError(f"Voice cloning failed after {elapsed:.0f}s")

    if "F5TTS_DONE" not in r.stdout:
        raise VoiceCloneError("F5-TTS did not complete")

    to_wav2lip_audio(raw_out, output_path)
    dur = audio_duration(output_path)
    logger.info(f"✓ F5-TTS: {dur:.1f}s speech in {elapsed:.0f}s")
    return output_path


# ══════════════════════════════════════════════════════════════════════════════
# UNIFIED INTERFACE
# ══════════════════════════════════════════════════════════════════════════════

def generate_speech(
    script: str,
    reference_audio: str,
    output_path: str,
    reference_text: str = "",
    speed: float = 1.0,
    temp_dir: str = "temp",
    mode: str = "fast",
    voice: str = "en-US-GuyNeural",
) -> str:
    """
    Generate speech — unified interface for both engines.

    mode="fast"  → edge-tts (instant, no voice cloning)
    mode="clone" → F5-TTS (uses your voice sample, 2-5 min)
    """
    if not script or not script.strip():
        raise VoiceCloneError("Script is empty")

    if mode == "clone":
        try:
            return generate_speech_clone(
                script=script,
                reference_audio=reference_audio,
                output_path=output_path,
                reference_text=reference_text,
                speed=speed,
                temp_dir=temp_dir,
            )
        except VoiceCloneError as e:
            # If F5-TTS not installed or fails, fall back to edge-tts
            if "f5_tts" in str(e).lower() or "No module named 'f5_tts'" in str(e):
                logger.warning(f"F5-TTS not available, falling back to edge-tts: {e}")
                return generate_speech_fast(
                    script=script,
                    output_path=output_path,
                    voice=voice,
                    speed=speed,
                    temp_dir=temp_dir,
                )
            raise
    else:
        return generate_speech_fast(
            script=script,
            output_path=output_path,
            voice=voice,
            speed=speed,
            temp_dir=temp_dir,
        )
