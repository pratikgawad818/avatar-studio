"""Avatar upload and management endpoints."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
import shutil
import uuid
import json
from datetime import datetime

router = APIRouter(prefix="/avatars", tags=["avatars"])


def get_avatars_dir():
    """Get avatars directory path."""
    return Path(__file__).parent.parent.parent / "avatars"


@router.post("/upload")
async def upload_avatar(file: UploadFile = File(...), name: str = Form("My Avatar")):
    """Upload an avatar image (JPG/PNG/WEBP)."""
    avatars_dir = get_avatars_dir()
    avatars_dir.mkdir(exist_ok=True)
    
    ext = Path(file.filename).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="Only JPG/PNG/WEBP supported")
    
    aid = str(uuid.uuid4())[:8]
    dest = avatars_dir / f"{aid}{ext}"
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    meta = {
        "id": aid,
        "name": name,
        "file": dest.name,
        "url": f"/avatars_img/{dest.name}",
        "created": datetime.now().isoformat()
    }
    (avatars_dir / f"{aid}.json").write_text(json.dumps(meta))
    return {"ok": True, "avatar": meta}


@router.get("/list")
async def list_avatars():
    """List all avatars."""
    avatars_dir = get_avatars_dir()
    avatars = []
    for jf in sorted(avatars_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            m = json.loads(jf.read_text())
            if (avatars_dir / m["file"]).exists():
                avatars.append(m)
        except Exception:
            pass
    return {"avatars": avatars}


@router.delete("/{aid}")
async def delete_avatar(aid: str):
    """Delete an avatar by ID."""
    avatars_dir = get_avatars_dir()
    for f in avatars_dir.glob(f"{aid}*"):
        f.unlink(missing_ok=True)
    return {"ok": True}
