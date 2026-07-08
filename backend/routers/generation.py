"""
Video generation endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json

from database import get_db
from models import Job, JobStatus
from schemas import GenerationRequest, JobResponse, JobListResponse, EstimationRequest, EstimationResponse
from celery_app import generate_video_task
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/estimate", response_model=EstimationResponse)
async def estimate_generation(
    request: EstimationRequest,
):
    """Estimate video generation time"""
    words = len(request.script.strip().split())
    
    # Estimation logic (simplified)
    if request.voice_mode == "clone":
        voice_sec = words * 0.5  # F5-TTS is faster
    else:
        voice_sec = words * 0.3  # Edge-TTS estimate
    
    lip_sec = max(60, int(words * 2.5))
    comp_sec = 30
    total = int(voice_sec + lip_sec + comp_sec)
    
    warning = None
    if words > 100:
        warning = f"Script is long ({words} words). Consider under 50 words for faster results."
    
    return {
        "word_count": words,
        "estimated_seconds": total,
        "estimated_minutes": round(total / 60, 1),
        "breakdown": {
            "voice": int(voice_sec),
            "lipsync": int(lip_sec),
            "composite": comp_sec,
        },
        "warning": warning,
    }


@router.post("/generate", response_model=JobResponse)
async def generate_video(
    request: GenerationRequest,
    user_id: str = "demo-user",  # Would come from JWT
    db: AsyncSession = Depends(get_db),
):
    """Start video generation job"""
    # Create job record
    job = Job(
        user_id=user_id,
        project_id=request.project_id,
        status=JobStatus.PENDING,
        script=request.script,
        avatar_id=request.avatar_id,
        voice_id=request.voice_id,
        background_id=request.background_id,
        voice_mode=request.voice_mode,
        resolution=request.resolution,
        aspect_ratio=request.aspect_ratio,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Start Celery task
    config = request.dict()
    task = generate_video_task.delay(job.id, config)
    
    logger.info(f"Generation job created: {job.id}")
    return job


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get job status and progress"""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    
    return job


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    skip: int = 0,
    limit: int = 20,
    user_id: str = "demo-user",  # Would come from JWT
    db: AsyncSession = Depends(get_db),
):
    """List user's generation jobs"""
    result = await db.execute(
        select(Job)
        .where(Job.user_id == user_id)
        .order_by(Job.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    jobs = result.scalars().all()
    
    count_result = await db.execute(select(Job).where(Job.user_id == user_id))
    total = len(count_result.scalars().all())
    
    return {"jobs": jobs, "total": total}


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Cancel a running job"""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    
    if job.status != JobStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only running jobs can be cancelled",
        )
    
    job.status = JobStatus.CANCELLED
    job.error_message = "Cancelled by user"
    await db.commit()
    
    return {"ok": True}
