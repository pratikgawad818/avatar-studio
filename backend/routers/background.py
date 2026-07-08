"""Background upload and management endpoints."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil
import uuid

router = APIRouter(prefix="/backgrounds", tags=["backgrounds"])


def get_backgrounds_dir():
    """Get backgrounds directory path."""
    return Path(__file__).parent.parent.parent / "backgrounds"


@router.post("/upload")
async def upload_background(file: UploadFile = File(...)):
    """Upload a background image or video (JPG/PNG/MP4/MOV)."""
    bg_dir = get_backgrounds_dir()
    bg_dir.mkdir(exist_ok=True)
    
    ext = Path(file.filename).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".mp4", ".mov"}:
        raise HTTPException(status_code=400, detail="JPG/PNG/MP4/MOV only")
    
    bid = str(uuid.uuid4())[:8]
    dest = bg_dir / f"{bid}{ext}"
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    return {
        "ok": True,
        "id": bid,
        "url": f"/backgrounds_img/{dest.name}",
        "file": dest.name
    }


@router.get("/list")
async def list_backgrounds():
    """List all backgrounds."""
    bg_dir = get_backgrounds_dir()
    items = []
    for f in sorted(bg_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".mp4", ".mov"}:
            items.append({
                "name": f.name,
                "url": f"/backgrounds_img/{f.name}",
                "type": "video" if f.suffix.lower() in {".mp4", ".mov"} else "image",
            })
    return {"backgrounds": items}
