"""
Avatar Studio - Celery Setup
Asynchronous task queue for video generation
"""

from celery import Celery
from config import settings
import logging

logger = logging.getLogger(__name__)

app = Celery(
    "avatar_studio",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # Hard limit: 1 hour
    task_soft_time_limit=3300,  # Soft limit: 55 minutes
)


@app.task(bind=True, name="generate_video")
def generate_video_task(self, job_id: str, config: dict):
    """
    Async task to generate video
    
    Args:
        job_id: Database job ID
        config: Generation configuration dict
    """
    try:
        logger.info(f"Starting video generation for job {job_id}")
        # Import pipeline here to avoid circular imports
        from pipeline.orchestrator import generate_video_pipeline
        
        result = generate_video_pipeline(
            job_id=job_id,
            config=config,
            progress_callback=self.update_state,
        )
        
        logger.info(f"Video generation completed for job {job_id}")
        return {"status": "completed", "job_id": job_id, "output": result}
    
    except Exception as e:
        logger.exception(f"Error generating video for job {job_id}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "job_id": job_id}
        )
        raise
