"""
pipeline/compositor.py
Composite avatar on background, burn subtitles, produce final MP4.
Compatible with FFmpeg 8.x (no -loop flag for images).
"""
import os, subprocess, logging, shutil
from pathlib import Path

logger = logging.getLogger(__name__)

POSITION_MAP = {
    "center":       ("(W-w)/2", "(H-h)/2"),
    "lower_center": ("(W-w)/2", "H-h-40"),
    "lower_left":   ("40",      "H-h-40"),
    "lower_right":  ("W-w-40",  "H-h-40"),
    "upper_center": ("(W-w)/2", "40"),
}


def _duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, timeout=10)
    try:
        return float(r.stdout.strip())
    except (ValueError, AttributeError):
        return 30.0


def _run(cmd: list, label: str, timeout: int = 120):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"{label} failed:\n{r.stderr[-1500:]}")


# ── Gradient background ──────────────────────────────────────────────────────

def make_gradient_bg(out: str, duration: float, res=(1280, 720)):
    W, H = res
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    cmd = ["ffmpeg", "-y", "-f", "lavfi",
           "-i", f"color=0x1a1a2e:s={W}x{H}:r=25:d={duration}",
           "-c:v", "libx264", "-preset", "fast", out]
    r = subprocess.run(cmd, capture_output=True, timeout=30)
    if r.returncode != 0:
        # Fallback
        cmd2 = ["ffmpeg", "-y", "-f", "lavfi",
                "-i", f"color=0x0d0d1a:s={W}x{H}:r=25:d={duration}",
                "-c:v", "libx264", "-preset", "fast", out]
        subprocess.run(cmd2, capture_output=True, check=True, timeout=30)
    logger.info(f"Background: {out}")


# ── Composite ────────────────────────────────────────────────────────────────

def composite(avatar: str, background: str, out: str,
              scale: float = 0.55, position: str = "center",
              res=(1280, 720), vignette: bool = True) -> str:
    """
    Composite avatar video on background (image or video).
    FFmpeg 8.x compatible.
    """
    W, H = res
    aw = int(W * scale)
    px, py = POSITION_MAP.get(position, POSITION_MAP["center"])
    dur = _duration(avatar)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    is_video_bg = Path(background).suffix.lower() in {".mp4", ".mov", ".avi", ".webm"}
    vig = ",vignette=PI/5" if vignette else ""

    # Check if avatar has audio
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=codec_type", "-of", "csv=p=0", avatar],
        capture_output=True, text=True, timeout=5
    )
    has_audio = "audio" in (probe.stdout or "")

    if is_video_bg:
        # Video background
        fc = (
            f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H}{vig}[bg];"
            f"[1:v]scale={aw}:-2[av];"
            f"[bg][av]overlay={px}:{py}:shortest=1[out]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", background,
            "-i", avatar,
            "-filter_complex", fc,
            "-map", "[out]",
        ]
    else:
        # Image background: use lavfi color as timeline, overlay image then avatar
        fc = (
            f"[2:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H}{vig}[bgimg];"
            f"[0:v][bgimg]overlay=0:0[bg];"
            f"[1:v]scale={aw}:-2[av];"
            f"[bg][av]overlay={px}:{py}[out]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=black:s={W}x{H}:r=25:d={dur}",
            "-i", avatar,
            "-i", background,
            "-filter_complex", fc,
            "-map", "[out]",
        ]

    # Add audio mapping if available
    if has_audio:
        cmd += ["-map", "1:a", "-c:a", "aac", "-b:a", "192k"]

    cmd += [
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-movflags", "+faststart",
        "-t", str(dur), out
    ]

    _run(cmd, "composite")
    logger.info(f"Composited: {out}")
    return out


# ── Lower-third name bar ─────────────────────────────────────────────────────

def add_lower_third(video: str, out: str,
                    name: str = "", title: str = "",
                    duration: float = 4.0, start: float = 0.5) -> str:
    if not name and not title:
        return video
    end = start + duration
    filters = [
        f"drawbox=x=0:y=ih-90:w=iw:h=90:color=0x000000@0.7:t=fill"
        f":enable='between(t,{start},{end})'",
    ]
    if name:
        filters.append(
            f"drawtext=text='{_esc(name)}':fontsize=30:fontcolor=white"
            f":x=40:y=ih-72:enable='between(t,{start},{end})'")
    if title:
        filters.append(
            f"drawtext=text='{_esc(title)}':fontsize=20:fontcolor=lightgray"
            f":x=40:y=ih-42:enable='between(t,{start},{end})'")
    cmd = ["ffmpeg", "-y", "-i", video,
           "-vf", ",".join(filters),
           "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "copy", out]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        logger.warning(f"Lower-third failed: {r.stderr[:300]}")
        return video
    return out


def _esc(t: str) -> str:
    return t.replace("'", "\\'").replace(":", "\\:").replace(",", "\\,")


# ── Subtitles ────────────────────────────────────────────────────────────────

def _srt_ts(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    ms = int(round((s - int(s)) * 1000))
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def script_to_srt(script: str, duration: float, srt_path: str, wpl: int = 8) -> str:
    words = script.split()
    chunks = [" ".join(words[i:i+wpl]) for i in range(0, len(words), wpl)]
    os.makedirs(os.path.dirname(srt_path) or ".", exist_ok=True)
    with open(srt_path, "w") as f:
        t = 0.2
        for i, chunk in enumerate(chunks):
            prop = len(chunk.split()) / max(len(words), 1)
            dur = max(prop * duration - 0.1, 0.8)
            end = min(t + dur, duration - 0.1)
            f.write(f"{i+1}\n{_srt_ts(t)} --> {_srt_ts(end)}\n{chunk}\n\n")
            t = end + 0.1
    return srt_path


def whisper_to_srt(audio: str, srt_path: str, model: str = "base", lang: str = "en") -> str:
    import whisper
    logger.info(f"Whisper transcription (model={model})...")
    m = whisper.load_model(model)
    result = m.transcribe(audio, language=lang, word_timestamps=True, verbose=False)
    os.makedirs(os.path.dirname(srt_path) or ".", exist_ok=True)
    entries, idx = [], 0
    for seg in result.get("segments", []):
        words = seg.get("words", [])
        WPL = 8
        for j in range(0, max(len(words), 1), WPL):
            grp = words[j:j+WPL]
            text = " ".join(w["word"].strip() for w in grp)
            start = grp[0]["start"] if grp else seg["start"]
            end = grp[-1]["end"] if grp else seg["end"]
            entries.append((idx+1, start, end, text))
            idx += 1
    with open(srt_path, "w") as f:
        for n, s, e, t in entries:
            f.write(f"{n}\n{_srt_ts(s)} --> {_srt_ts(e)}\n{t}\n\n")
    logger.info(f"SRT: {len(entries)} entries")
    return srt_path


def burn_subtitles(video: str, srt: str, out: str,
                   style: str = "netflix", margin: int = 60) -> str:
    """
    Burn subtitles onto video.
    Tries drawtext first, falls back to copying video without subs.
    Note: requires ffmpeg compiled with --enable-libfreetype for drawtext.
    Install with: brew install ffmpeg-full (or use subtitles=False)
    """
    # Check if drawtext is available
    check = subprocess.run(["ffmpeg", "-filters"], capture_output=True, text=True, timeout=5)
    has_drawtext = "drawtext" in (check.stdout or "")

    if not has_drawtext:
        logger.warning("FFmpeg missing drawtext filter — subtitles skipped. Install ffmpeg-full for subtitle support.")
        return video

    # Parse SRT
    entries = _parse_srt(srt)
    if not entries:
        logger.warning("No subtitle entries found")
        return video

    # Style configs
    STYLES = {
        "netflix":    {"fontsize": 28, "fontcolor": "white", "borderw": 2, "shadowx": 1, "shadowy": 1, "box": 1, "boxcolor": "black@0.6", "boxborderw": 8},
        "bold_white": {"fontsize": 32, "fontcolor": "white", "borderw": 3, "shadowx": 0, "shadowy": 0, "box": 0},
        "yellow":     {"fontsize": 28, "fontcolor": "yellow", "borderw": 2, "shadowx": 1, "shadowy": 1, "box": 0},
    }
    s = STYLES.get(style, STYLES["netflix"])

    filters = []
    for start, end, text in entries[:20]:  # Max 20 to avoid filter complexity limits
        escaped = text.replace("'", "'\\''").replace(":", "\\:").replace(",", "\\,").replace("%", "\\%")
        f = (
            f"drawtext=text='{escaped}'"
            f":fontsize={s['fontsize']}:fontcolor={s['fontcolor']}"
            f":borderw={s['borderw']}"
            f":x=(w-text_w)/2:y=h-{margin}-text_h"
            f":enable='between(t,{start:.3f},{end:.3f})'"
        )
        if s.get('box'):
            f += f":box=1:boxcolor={s['boxcolor']}:boxborderw={s['boxborderw']}"
        filters.append(f)

    vf = ",".join(filters)
    cmd = ["ffmpeg", "-y", "-i", video, "-vf", vf,
           "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "copy", out]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        logger.warning(f"Subtitle burn failed — skipping. Install ffmpeg-full for subtitle support.")
        return video
    logger.info(f"Subtitles burned: {out} ({len(entries)} entries)")
    return out


def _parse_srt(path: str) -> list:
    """Parse SRT file into [(start_sec, end_sec, text), ...]"""
    entries = []
    try:
        with open(path) as f:
            content = f.read()
        blocks = content.strip().split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue
            timecode = lines[1]
            text = " ".join(lines[2:])
            parts = timecode.split(" --> ")
            if len(parts) == 2:
                start = _srt_to_sec(parts[0].strip())
                end = _srt_to_sec(parts[1].strip())
                entries.append((start, end, text))
    except Exception as e:
        logger.warning(f"SRT parse error: {e}")
    return entries


def _srt_to_sec(ts: str) -> float:
    """Convert SRT timestamp to seconds."""
    ts = ts.replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 0.0


# ── Full pipeline ────────────────────────────────────────────────────────────

def full_pipeline(
    avatar_video: str,
    audio_path: str,
    background: str | None,
    script: str,
    out_path: str,
    temp_dir: str = "temp",
    position: str = "center",
    scale: float = 0.55,
    res: tuple = (1280, 720),
    subtitles: bool = True,
    sub_style: str = "netflix",
    use_whisper: bool = True,
    whisper_model: str = "base",
    lower_name: str = "",
    lower_title: str = "",
) -> str:
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    dur = _duration(avatar_video)

    # Background
    if not background or not Path(background).exists():
        bg = os.path.join(temp_dir, "gradient.mp4")
        make_gradient_bg(bg, dur, res)
        background = bg

    # Composite
    comp = os.path.join(temp_dir, "composited.mp4")
    composite(avatar_video, background, comp, scale, position, res)

    # Lower third
    if lower_name or lower_title:
        lt_out = os.path.join(temp_dir, "with_lt.mp4")
        comp = add_lower_third(comp, lt_out, lower_name, lower_title)

    # Subtitles
    if subtitles:
        srt = os.path.join(temp_dir, "subs.srt")
        try:
            if use_whisper:
                whisper_to_srt(audio_path, srt, model=whisper_model)
            else:
                script_to_srt(script, dur, srt)
        except Exception as e:
            logger.warning(f"Subtitle generation failed: {e} — using script fallback")
            script_to_srt(script, dur, srt)
        sub_out = os.path.join(temp_dir, "subtitled.mp4")
        comp = burn_subtitles(comp, srt, sub_out, sub_style)

    shutil.copy2(comp, out_path)
    logger.info(f"Final video: {out_path}")
    return out_path
