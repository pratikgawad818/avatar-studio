"""Voice recording and upload endpoints."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import shutil
import uuid
import json
import subprocess
from datetime import datetime

router = APIRouter(prefix="/voices", tags=["voices"])


def get_voices_dir():
    """Get voices directory path."""
    return Path(__file__).parent.parent.parent / "voices"


def _probe_duration(path: str) -> float:
    """Get audio duration using ffprobe."""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


@router.post("/save")
async def save_voice_recording(
    audio: UploadFile = File(...),
    name: str = Form("My Voice"),
):
    """Save a voice recording (WebM/WAV)."""
    voices_dir = get_voices_dir()
    voices_dir.mkdir(exist_ok=True)
    
    vid = str(uuid.uuid4())[:8]
    suffix = Path(audio.filename or "recording.webm").suffix or ".webm"
    raw_path = voices_dir / f"{vid}_raw{suffix}"
    
    with open(raw_path, "wb") as f:
        shutil.copyfileobj(audio.file, f)
    
    wav_path = voices_dir / f"{vid}.wav"
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw_path),
         "-ac", "1", "-ar", "22050", "-acodec", "pcm_s16le", str(wav_path)],
        capture_output=True,
    )
    raw_path.unlink(missing_ok=True)
    
    if r.returncode != 0:
        raise HTTPException(status_code=400, detail="Audio conversion failed")
    
    meta = {
        "id": vid,
        "name": name,
        "file": wav_path.name,
        "created": datetime.now().isoformat(),
        "duration": round(_probe_duration(str(wav_path)), 1)
    }
    (voices_dir / f"{vid}.json").write_text(json.dumps(meta))
    return {"ok": True, "voice": meta}


@router.post("/upload")
async def upload_voice(file: UploadFile = File(...), name: str = Form("Uploaded Voice")):
    """Upload a voice file (WAV/MP3/M4A/OGG/FLAC/WEBM)."""
    voices_dir = get_voices_dir()
    voices_dir.mkdir(exist_ok=True)
    
    ext = Path(file.filename).suffix.lower()
    if ext not in {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}:
        raise HTTPException(status_code=400, detail="Unsupported format")
    
    vid = str(uuid.uuid4())[:8]
    raw = voices_dir / f"{vid}_raw{ext}"
    with open(raw, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    wav = voices_dir / f"{vid}.wav"
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw),
         "-ac", "1", "-ar", "22050", "-acodec", "pcm_s16le", str(wav)],
        capture_output=True,
    )
    raw.unlink(missing_ok=True)
    
    if r.returncode != 0:
        raise HTTPException(status_code=400, detail="Audio conversion failed")
    
    meta = {
        "id": vid,
        "name": name,
        "file": wav.name,
        "created": datetime.now().isoformat(),
        "duration": round(_probe_duration(str(wav)), 1)
    }
    (voices_dir / f"{vid}.json").write_text(json.dumps(meta))
    return {"ok": True, "voice": meta}


@router.get("/list")
async def list_voices():
    """List all uploaded voices."""
    voices_dir = get_voices_dir()
    voices = []
    for jf in sorted(voices_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            m = json.loads(jf.read_text())
            if (voices_dir / m["file"]).exists():
                m["url"] = f"/voices_audio/{m['file']}"
                voices.append(m)
        except Exception:
            pass
    return {"voices": voices}


@router.delete("/{vid}")
async def delete_voice(vid: str):
    """Delete a voice by ID."""
    voices_dir = get_voices_dir()
    for f in voices_dir.glob(f"{vid}*"):
        f.unlink(missing_ok=True)
    return {"ok": True}


@router.get("/audio/{filename}")
async def serve_voice(filename: str):
    """Serve voice audio file."""
    voices_dir = get_voices_dir()
    p = voices_dir / filename
    if p.exists():
        return FileResponse(str(p), media_type="audio/wav")
    raise HTTPException(status_code=404, detail="Not found")
