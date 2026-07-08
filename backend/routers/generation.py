"""Video generation endpoints."""

from fastapi import APIRouter, Form, HTTPException, BackgroundTasks
from pathlib import Path
import json
from datetime import datetime
import time
import os
import logging

router = APIRouter(prefix="/generation", tags=["generation"])
logger = logging.getLogger("studio")


class JobManager:
    """Manages video generation jobs."""
    def __init__(self):
        self.current_job = None
    
    def is_running(self):
        return self.current_job and self.current_job.get("status") == "running"


job_manager = JobManager()


@router.post("/estimate")
async def estimate_time(script: str = Form(...)):
    """Estimate video generation time based on script length."""
    words = len(script.strip().split())
    # Rough estimates
    voice_sec = int(words * 0.3)  # ~0.3s per word for TTS
    lip_sec = max(60, int(words * 2.5))  # ~2.5s per word for Wav2Lip
    comp_sec = 30  # Compositing
    total = voice_sec + lip_sec + comp_sec
    
    return {
        "words": words,
        "estimated_seconds": total,
        "estimated_minutes": round(total / 60, 1),
        "breakdown": {
            "voice": voice_sec,
            "lipsync": lip_sec,
            "composite": comp_sec
        },
        "warning": f"Script is long ({words} words). Consider under 50 words for faster results." if words > 100 else None,
    }


@router.post("/generate")
async def generate(
    background_tasks: BackgroundTasks,
    script: str = Form(...),
    voice_id: str = Form(...),
    avatar_id: str = Form(...),
    voice_transcript: str = Form(""),
    voice_speed: float = Form(1.0),
    voice_mode: str = Form("fast"),
    voice_edge: str = Form("en-US-GuyNeural"),
    position: str = Form("center"),
    avatar_scale: float = Form(0.75),
    resolution: str = Form("1920x1080"),
    subtitles: bool = Form(True),
    sub_style: str = Form("netflix"),
    use_whisper: bool = Form(True),
    whisper_model: str = Form("base"),
    lipsync_quality: str = Form("enhanced"),
    lower_name: str = Form(""),
    lower_title: str = Form(""),
    background_file: str = Form(""),
    aspect_ratio: str = Form("16:9"),
):
    """Start a new video generation job."""
    if job_manager.is_running():
        raise HTTPException(
            status_code=409,
            detail="Already generating. Please wait or cancel."
        )
    
    # Validate files exist
    voices_dir = Path(__file__).parent.parent.parent / "voices"
    avatars_dir = Path(__file__).parent.parent.parent / "avatars"
    bg_dir = Path(__file__).parent.parent.parent / "backgrounds"
    
    avatar_meta_f = avatars_dir / f"{avatar_id}.json"
    if not avatar_meta_f.exists():
        raise HTTPException(status_code=400, detail=f"Avatar {avatar_id} not found")
    
    # Start background job
    import uuid
    job_id = str(uuid.uuid4())[:8]
    job_manager.current_job = {
        "job_id": job_id,
        "status": "running",
        "progress": 0,
        "step": "Initializing..."
    }
    
    # TODO: Queue actual pipeline execution
    # background_tasks.add_task(_run_pipeline, cfg)
    
    return {"ok": True, "job_id": job_id}


@router.get("/status")
async def get_status():
    """Get current job status."""
    if not job_manager.current_job:
        return {
            "status": "idle",
            "progress": 0,
            "step": "Ready",
            "output_file": None,
            "error": None
        }
    return job_manager.current_job


@router.post("/cancel")
async def cancel_job():
    """Cancel the running generation job."""
    if not job_manager.is_running():
        return {"ok": False, "msg": "No running job to cancel"}
    
    job_manager.current_job["status"] = "cancelled"
    # TODO: Kill subprocesses
    return {"ok": True, "msg": "Job cancelled"}
