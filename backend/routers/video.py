"""Video output management endpoints."""

from fastapi import APIRouter, HTTPException
from pathlib import Path
from datetime import datetime

router = APIRouter(prefix="/videos", tags=["videos"])


def get_output_dir():
    """Get output directory path."""
    return Path(__file__).parent.parent.parent / "outputs"


@router.get("/list")
async def list_videos():
    """List all generated videos."""
    output_dir = get_output_dir()
    output_dir.mkdir(exist_ok=True)
    
    videos = []
    for f in sorted(output_dir.glob("video_*.mp4"), reverse=True):
        s = f.stat()
        videos.append({
            "filename": f.name,
            "url": f"/outputs/{f.name}",
            "size_mb": round(s.st_size / 1e6, 1),
            "created": datetime.fromtimestamp(s.st_mtime).strftime("%b %d %H:%M"),
        })
    return {"videos": videos}


@router.delete("/{name}")
async def delete_video(name: str):
    """Delete a video by filename."""
    output_dir = get_output_dir()
    p = output_dir / name
    
    if not p.exists() or p.suffix != ".mp4":
        raise HTTPException(status_code=404, detail="Not found")
    
    p.unlink()
    return {"ok": True}
