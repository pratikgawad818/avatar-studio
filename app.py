"""
Avatar Studio — app.py
FastAPI backend for a HeyGen-like local AI video studio.
"""

import os, sys, uuid, json, shutil, logging, asyncio, threading, signal
from pathlib import Path
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# ── Paths ────────────────────────────────────────────────────────────────────
BASE        = Path(__file__).parent
VOICES_DIR  = BASE / "voices"
AVATARS_DIR = BASE / "avatars"
BG_DIR      = BASE / "backgrounds"
OUTPUT_DIR  = BASE / "outputs"
TEMP_DIR    = BASE / "temp"
STATIC_DIR  = BASE / "static"

for d in [VOICES_DIR, AVATARS_DIR, BG_DIR, OUTPUT_DIR, TEMP_DIR, STATIC_DIR]:
    d.mkdir(exist_ok=True)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("studio")

# ── Pipeline path ────────────────────────────────────────────────────────────
sys.path.insert(0, str(BASE))

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="Avatar Studio", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
app.mount("/static",          StaticFiles(directory=STATIC_DIR, html=True), name="static")
app.mount("/outputs",         StaticFiles(directory=OUTPUT_DIR),             name="outputs")
app.mount("/avatars_img",     StaticFiles(directory=AVATARS_DIR),            name="avatars_img")
app.mount("/backgrounds_img", StaticFiles(directory=BG_DIR),                 name="bg_img")

# ── Job state ────────────────────────────────────────────────────────────────
class JobState:
    def __init__(self):
        self.reset_state()
        self._listeners: list = []
        self._lock = threading.Lock()

    def reset_state(self):
        self.job_id      = None
        self.status      = "idle"
        self.progress    = 0
        self.step        = ""
        self.steps_done  = []
        self.log_lines   = []
        self.output_file = None
        self.error       = None
        self.started_at  = None
        self._cancel     = False

    def reset(self):
        self.reset_state()
        self.job_id = str(uuid.uuid4())[:8]
        self.status = "running"
        self.started_at = datetime.now().isoformat()

    def cancel(self):
        self._cancel = True
        self.fail("Cancelled by user")

    @property
    def cancelled(self):
        return self._cancel

    def update(self, pct: int, step: str, log: str = ""):
        if self._cancel:
            raise RuntimeError("Cancelled by user")
        self.progress = pct
        self.step     = step
        if log:
            self.log_lines.append(log)
        self._push()

    def done(self, output: str):
        self.status      = "done"
        self.progress    = 100
        self.step        = "Complete!"
        self.output_file = output
        self._push()

    def fail(self, err: str):
        self.status = "error"
        self.step   = "Error"
        self.error  = err
        self.log_lines.append(f"ERROR: {err}")
        self._push()

    def _push(self):
        payload = dict(
            job_id=self.job_id, status=self.status,
            progress=self.progress, step=self.step,
            steps_done=self.steps_done,
            log=self.log_lines[-1] if self.log_lines else "",
            output_file=self.output_file, error=self.error,
            started_at=self.started_at,
        )
        with self._lock:
            for q in list(self._listeners):
                try:
                    q.put_nowait(payload)
                except asyncio.QueueFull:
                    pass

    def add_listener(self, q):
        with self._lock:
            self._listeners.append(q)

    def remove_listener(self, q):
        with self._lock:
            if q in self._listeners:
                self._listeners.remove(q)


JOB = JobState()

# ── Pages ────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse((STATIC_DIR / "index.html").read_text())


# ── Voice endpoints ──────────────────────────────────────────────────────────

@app.post("/voices/save")
async def save_voice_recording(
    audio: UploadFile = File(...),
    name:  str = Form("My Voice"),
):
    import subprocess
    vid      = str(uuid.uuid4())[:8]
    suffix   = Path(audio.filename or "recording.webm").suffix or ".webm"
    raw_path = VOICES_DIR / f"{vid}_raw{suffix}"
    with open(raw_path, "wb") as f:
        shutil.copyfileobj(audio.file, f)

    wav_path = VOICES_DIR / f"{vid}.wav"
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw_path),
         "-ac", "1", "-ar", "22050", "-acodec", "pcm_s16le", str(wav_path)],
        capture_output=True,
    )
    raw_path.unlink(missing_ok=True)
    if r.returncode != 0:
        return JSONResponse({"error": "Audio conversion failed"}, status_code=400)

    meta = {"id": vid, "name": name, "file": wav_path.name,
            "created": datetime.now().isoformat(),
            "duration": round(_probe_duration(str(wav_path)), 1)}
    (VOICES_DIR / f"{vid}.json").write_text(json.dumps(meta))
    return {"ok": True, "voice": meta}


@app.post("/voices/upload")
async def upload_voice(file: UploadFile = File(...), name: str = Form("Uploaded Voice")):
    import subprocess
    ext = Path(file.filename).suffix.lower()
    if ext not in {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}:
        return JSONResponse({"error": "Unsupported format"}, status_code=400)

    vid = str(uuid.uuid4())[:8]
    raw = VOICES_DIR / f"{vid}_raw{ext}"
    with open(raw, "wb") as f:
        shutil.copyfileobj(file.file, f)

    wav = VOICES_DIR / f"{vid}.wav"
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw),
         "-ac", "1", "-ar", "22050", "-acodec", "pcm_s16le", str(wav)],
        capture_output=True,
    )
    raw.unlink(missing_ok=True)
    if r.returncode != 0:
        return JSONResponse({"error": "Audio conversion failed"}, status_code=400)

    meta = {"id": vid, "name": name, "file": wav.name,
            "created": datetime.now().isoformat(),
            "duration": round(_probe_duration(str(wav)), 1)}
    (VOICES_DIR / f"{vid}.json").write_text(json.dumps(meta))
    return {"ok": True, "voice": meta}


@app.get("/voices/list")
async def list_voices():
    voices = []
    for jf in sorted(VOICES_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            m = json.loads(jf.read_text())
            if (VOICES_DIR / m["file"]).exists():
                m["url"] = f"/voices_audio/{m['file']}"
                voices.append(m)
        except Exception:
            pass
    return {"voices": voices}


@app.delete("/voices/{vid}")
async def delete_voice(vid: str):
    for f in VOICES_DIR.glob(f"{vid}*"):
        f.unlink(missing_ok=True)
    return {"ok": True}


@app.get("/voices_audio/{filename}")
async def serve_voice(filename: str):
    p = VOICES_DIR / filename
    if p.exists():
        return FileResponse(str(p), media_type="audio/wav")
    return JSONResponse({"error": "Not found"}, status_code=404)


# ── Avatar endpoints ─────────────────────────────────────────────────────────

@app.post("/avatars/upload")
async def upload_avatar(file: UploadFile = File(...), name: str = Form("My Avatar")):
    ext = Path(file.filename).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        return JSONResponse({"error": "Only JPG/PNG/WEBP supported"}, status_code=400)

    aid  = str(uuid.uuid4())[:8]
    dest = AVATARS_DIR / f"{aid}{ext}"
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    meta = {"id": aid, "name": name, "file": dest.name,
            "url": f"/avatars_img/{dest.name}",
            "created": datetime.now().isoformat()}
    (AVATARS_DIR / f"{aid}.json").write_text(json.dumps(meta))
    return {"ok": True, "avatar": meta}


@app.get("/avatars/list")
async def list_avatars():
    avatars = []
    for jf in sorted(AVATARS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            m = json.loads(jf.read_text())
            if (AVATARS_DIR / m["file"]).exists():
                avatars.append(m)
        except Exception:
            pass
    return {"avatars": avatars}


@app.delete("/avatars/{aid}")
async def delete_avatar(aid: str):
    for f in AVATARS_DIR.glob(f"{aid}*"):
        f.unlink(missing_ok=True)
    return {"ok": True}


# ── Background endpoints ──────────────────────────────────────────────────────

@app.post("/backgrounds/upload")
async def upload_background(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".mp4", ".mov"}:
        return JSONResponse({"error": "JPG/PNG/MP4/MOV only"}, status_code=400)

    bid  = str(uuid.uuid4())[:8]
    dest = BG_DIR / f"{bid}{ext}"
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"ok": True, "id": bid, "url": f"/backgrounds_img/{dest.name}", "file": dest.name}


@app.get("/backgrounds/list")
async def list_backgrounds():
    items = []
    for f in sorted(BG_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".mp4", ".mov"}:
            items.append({
                "name": f.name,
                "url":  f"/backgrounds_img/{f.name}",
                "type": "video" if f.suffix.lower() in {".mp4", ".mov"} else "image",
            })
    return {"backgrounds": items}


# ── Estimate endpoint ─────────────────────────────────────────────────────────

@app.post("/estimate")
async def estimate_time(script: str = Form(...)):
    """Return estimated generation time based on word count."""
    from pipeline.voice_clone import estimate_generation_time
    words = len(script.strip().split())
    voice_sec = estimate_generation_time(words)
    lip_sec   = max(60, int(words * 2.5))  # ~2.5s per word for Wav2Lip
    comp_sec  = 30
    total     = voice_sec + lip_sec + comp_sec
    return {
        "words": words,
        "estimated_seconds": total,
        "estimated_minutes": round(total / 60, 1),
        "breakdown": {"voice": voice_sec, "lipsync": lip_sec, "composite": comp_sec},
        "warning": f"Script is long ({words} words). Consider under 50 words for faster results." if words > 100 else None,
    }


# ── Generate ─────────────────────────────────────────────────────────────────

@app.post("/generate")
async def generate(
    background_tasks: BackgroundTasks,
    script:           str   = Form(...),
    voice_id:         str   = Form(...),
    avatar_id:        str   = Form(...),
    voice_transcript: str   = Form(""),
    voice_speed:      float = Form(1.0),
    voice_mode:       str   = Form("fast"),
    voice_edge:       str   = Form("en-US-GuyNeural"),
    position:         str   = Form("center"),
    avatar_scale:     float = Form(0.55),
    resolution:       str   = Form("1280x720"),
    subtitles:        bool  = Form(True),
    sub_style:        str   = Form("netflix"),
    use_whisper:      bool  = Form(True),
    whisper_model:    str   = Form("base"),
    lipsync_quality:  str   = Form("enhanced"),
    lower_name:       str   = Form(""),
    lower_title:      str   = Form(""),
    background_file:  str   = Form(""),
    aspect_ratio:     str   = Form("16:9"),
):
    if JOB.status == "running":
        return JSONResponse({"error": "Already generating. Please wait or cancel."}, status_code=409)

    voice_meta_f  = VOICES_DIR  / f"{voice_id}.json"
    avatar_meta_f = AVATARS_DIR / f"{avatar_id}.json"
    if voice_mode == "clone" and not voice_meta_f.exists():
        return JSONResponse({"error": f"Voice {voice_id} not found"}, status_code=400)
    if not avatar_meta_f.exists():
        return JSONResponse({"error": f"Avatar {avatar_id} not found"}, status_code=400)

    voice_file = ""
    if voice_mode == "clone" and voice_meta_f.exists():
        voice_file = str(VOICES_DIR / json.loads(voice_meta_f.read_text())["file"])
    avatar_file = AVATARS_DIR / json.loads(avatar_meta_f.read_text())["file"]

    bg_path = ""
    if background_file:
        p = BG_DIR / background_file
        if p.exists():
            bg_path = str(p)

    try:
        w, h = [int(x) for x in resolution.split("x")]
    except Exception:
        w, h = 1280, 720

    # Override with aspect ratio if provided
    RATIOS = {
        "16:9": (1280, 720), "9:16": (720, 1280), "1:1": (720, 720),
        "4:3": (960, 720), "4:5": (720, 900),
    }
    if aspect_ratio in RATIOS:
        base_w, base_h = RATIOS[aspect_ratio]
        # Scale to match resolution quality
        if resolution == "1920x1080":
            scale = 1.5
        elif resolution == "854x480":
            scale = 0.67
        else:
            scale = 1.0
        w, h = int(base_w * scale), int(base_h * scale)
        # Ensure even numbers
        w, h = w - (w % 2), h - (h % 2)

    cfg = dict(
        script=script.strip(),
        voice_file=voice_file,
        avatar_file=str(avatar_file),
        voice_transcript=voice_transcript,
        voice_speed=voice_speed,
        voice_mode=voice_mode,
        voice_edge=voice_edge,
        position=position,
        avatar_scale=avatar_scale,
        res=(w, h),
        subtitles=subtitles,
        sub_style=sub_style,
        use_whisper=use_whisper,
        whisper_model=whisper_model,
        lipsync_quality=lipsync_quality,
        lower_name=lower_name,
        lower_title=lower_title,
        bg_path=bg_path,
    )

    JOB.reset()
    background_tasks.add_task(_run_pipeline, cfg)
    return {"ok": True, "job_id": JOB.job_id}


# ── Cancel ───────────────────────────────────────────────────────────────────

@app.post("/cancel")
async def cancel_job():
    """Cancel the running generation job."""
    if JOB.status != "running":
        return {"ok": False, "msg": "No running job to cancel"}
    JOB.cancel()
    # Kill any F5-TTS or Wav2Lip subprocesses
    import subprocess
    try:
        r = subprocess.run(
            ["pkill", "-f", "F5TTS|wav2lip|inference.py"],
            capture_output=True, timeout=5
        )
    except Exception:
        pass
    return {"ok": True, "msg": "Job cancelled"}


# ── Pipeline ─────────────────────────────────────────────────────────────────

def _run_pipeline(cfg: dict):
    try:
        _pipeline(cfg)
    except RuntimeError as e:
        if "Cancelled" in str(e):
            logger.info("Pipeline cancelled by user")
        else:
            logger.exception("Pipeline error")
            JOB.fail(str(e))
    except Exception as e:
        logger.exception("Pipeline error")
        JOB.fail(str(e))


def _pipeline(cfg: dict):
    import time
    from pipeline.voice_clone import generate_speech, audio_duration, estimate_generation_time
    from pipeline.lip_sync    import photo_to_video, run_wav2lip
    from pipeline.compositor  import full_pipeline

    if os.environ.get("PYTHONHASHSEED", "x").strip() == "":
        del os.environ["PYTHONHASHSEED"]

    temp = str(TEMP_DIR)
    t0 = time.time()

    def el():
        return f"[{time.time() - t0:.0f}s]"

    word_count = len(cfg["script"].split())
    voice_mode = cfg.get("voice_mode", "fast")
    est_total = estimate_generation_time(word_count, voice_mode) + max(60, int(word_count * 2.5)) + 30

    # ── Voice Clone ──────────────────────────────────────────────────────
    mode_label = "edge-tts (fast)" if voice_mode == "fast" else "F5-TTS (clone)"
    JOB.update(2, f"Starting voice: {mode_label}...",
               f"{el()} Pipeline start — {word_count} words, mode={voice_mode}, est. ~{est_total // 60}min")
    JOB.update(5, "Preparing audio...",
               f"{el()} Voice engine: {mode_label}")

    audio_out = str(TEMP_DIR / "speech.wav")
    JOB.update(10, f"Generating speech ({mode_label})...",
               f"{el()} Generating {word_count} words via {mode_label}")

    voice_t = time.time()
    generate_speech(
        script=cfg["script"],
        reference_audio=cfg["voice_file"],
        output_path=audio_out,
        reference_text=cfg["voice_transcript"],
        speed=cfg["voice_speed"],
        temp_dir=temp,
        mode=voice_mode,
        voice=cfg.get("voice_edge", "en-US-GuyNeural"),
    )
    voice_sec = time.time() - voice_t
    dur = audio_duration(audio_out)

    JOB.steps_done.append("voice")
    JOB.update(28, f"Voice done — {dur:.1f}s audio ({voice_sec:.0f}s)",
               f"{el()} ✓ Voice: {dur:.1f}s speech in {voice_sec:.0f}s")

    # ── Lip Sync ─────────────────────────────────────────────────────────
    JOB.update(30, "Creating video from photo...",
               f"{el()} Photo → {dur:.1f}s silent video loop")

    base_vid = str(TEMP_DIR / "base.mp4")
    photo_to_video(cfg["avatar_file"], dur, base_vid, size=(512, 512))

    JOB.update(33, "Starting Wav2Lip...",
               f"{el()} ✓ Base video ready")

    frames = int(dur * 25)
    JOB.update(36, f"Wav2Lip: processing {frames} frames...",
               f"{el()} Wav2Lip: {frames} frames, batch_size=128")
    JOB.update(40, "Wav2Lip running (longest step)...",
               f"{el()} Face detection + lip generation in progress")

    lip_t = time.time()
    lipsync_out = str(TEMP_DIR / "lipsync.mp4")
    run_wav2lip(
        face_video=base_vid,
        audio=audio_out,
        out=lipsync_out,
        quality=cfg["lipsync_quality"],
        temp_dir=temp,
    )
    lip_sec = time.time() - lip_t

    JOB.steps_done.append("lipsync")
    JOB.update(70, f"Lip sync done ({lip_sec:.0f}s)",
               f"{el()} ✓ Lip sync: {frames} frames in {lip_sec:.0f}s")

    # ── Composite ────────────────────────────────────────────────────────
    bg_type = "custom" if cfg["bg_path"] else "gradient"
    JOB.update(72, f"Compositing ({bg_type} background)...",
               f"{el()} Composite: {bg_type} bg, pos={cfg['position']}, scale={cfg['avatar_scale']*100:.0f}%")

    JOB.steps_done.append("background")

    if cfg["subtitles"]:
        method = "Whisper AI" if cfg["use_whisper"] else "script timing"
        JOB.update(78, f"Generating subtitles ({method})...",
                   f"{el()} Subtitles via {method}")

    comp_t = time.time()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    final = str(OUTPUT_DIR / f"video_{ts}.mp4")

    full_pipeline(
        avatar_video  = lipsync_out,
        audio_path    = audio_out,
        background    = cfg["bg_path"] or None,
        script        = cfg["script"],
        out_path      = final,
        temp_dir      = temp,
        position      = cfg["position"],
        scale         = cfg["avatar_scale"],
        res           = cfg["res"],
        subtitles     = cfg["subtitles"],
        sub_style     = cfg["sub_style"],
        use_whisper   = cfg["use_whisper"],
        whisper_model = cfg["whisper_model"],
        lower_name    = cfg["lower_name"],
        lower_title   = cfg["lower_title"],
    )
    comp_sec = time.time() - comp_t

    JOB.steps_done += ["subtitles", "done"]
    JOB.update(95, f"Composite done ({comp_sec:.0f}s)",
               f"{el()} ✓ Composite + subs in {comp_sec:.0f}s")

    # ── Cleanup ──────────────────────────────────────────────────────────
    JOB.update(97, "Cleaning up...", f"{el()} Removing temp files")
    for pat in ["*.mp4", "*.wav", "*.avi", "*.srt", "*.webm"]:
        for f in TEMP_DIR.glob(pat):
            try:
                f.unlink()
            except Exception:
                pass

    total = time.time() - t0
    JOB.update(99, "Done!",
               f"{el()} ✓ TOTAL: {total:.0f}s — Voice {voice_sec:.0f}s | Lip {lip_sec:.0f}s | Comp {comp_sec:.0f}s")

    JOB.done(f"/outputs/{Path(final).name}")


# ── SSE progress ──────────────────────────────────────────────────────────────

@app.get("/progress")
async def sse_progress():
    q: asyncio.Queue = asyncio.Queue(maxsize=60)
    JOB.add_listener(q)

    async def gen() -> AsyncGenerator[str, None]:
        try:
            current = dict(
                job_id=JOB.job_id, status=JOB.status, progress=JOB.progress,
                step=JOB.step, steps_done=JOB.steps_done,
                log=JOB.log_lines[-1] if JOB.log_lines else "",
                output_file=JOB.output_file, error=JOB.error,
                started_at=JOB.started_at,
            )
            yield f"data: {json.dumps(current)}\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=20.0)
                    yield f"data: {json.dumps(payload)}\n\n"
                    if payload.get("status") in ("done", "error"):
                        break
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'heartbeat': True})}\n\n"
        finally:
            JOB.remove_listener(q)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/status")
async def status():
    return dict(
        status=JOB.status, progress=JOB.progress,
        step=JOB.step, output_file=JOB.output_file, error=JOB.error,
        started_at=JOB.started_at,
    )


# ── Videos ───────────────────────────────────────────────────────────────────

@app.get("/videos")
async def list_videos():
    videos = []
    for f in sorted(OUTPUT_DIR.glob("video_*.mp4"), reverse=True):
        s = f.stat()
        videos.append({
            "filename": f.name,
            "url":      f"/outputs/{f.name}",
            "size_mb":  round(s.st_size / 1e6, 1),
            "created":  datetime.fromtimestamp(s.st_mtime).strftime("%b %d %H:%M"),
        })
    return {"videos": videos}


@app.delete("/videos/{name}")
async def delete_video(name: str):
    p = OUTPUT_DIR / name
    if p.exists() and p.suffix == ".mp4":
        p.unlink()
        return {"ok": True}
    return JSONResponse({"error": "Not found"}, status_code=404)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _probe_duration(path: str) -> float:
    import subprocess
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


if __name__ == "__main__":
    import uvicorn
    print("\n  Avatar Studio  →  http://localhost:8002\n")
    uvicorn.run("app:app", host="0.0.0.0", port=8002, reload=False)
