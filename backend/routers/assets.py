"""
Asset management endpoints (avatars, voices, backgrounds)
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
import uuid
import logging

from database import get_db
from models import Asset, AssetType
from schemas import AssetResponse, AssetListResponse
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def get_asset_directory(asset_type: AssetType) -> Path:
    """Get directory for asset type"""
    dirs = {
        AssetType.AVATAR: Path(settings.AVATARS_DIR),
        AssetType.VOICE: Path(settings.VOICES_DIR),
        AssetType.BACKGROUND: Path(settings.BACKGROUNDS_DIR),
    }
    dir_path = dirs.get(asset_type)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


@router.post("/avatars/upload", response_model=AssetResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    name: str = Form("My Avatar"),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new avatar image"""
    # Validate file type
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG/PNG/WEBP images supported",
        )
    
    # Save file
    asset_dir = get_asset_directory(AssetType.AVATAR)
    file_id = str(uuid.uuid4())[:8]
    file_ext = Path(file.filename).suffix
    file_path = asset_dir / f"{file_id}{file_ext}"
    
    try:
        content = await file.read()
        file_path.write_bytes(content)
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed",
        )
    
    # Create asset record
    asset = Asset(
        asset_type=AssetType.AVATAR,
        name=name,
        file_path=str(file_path),
        file_size_mb=len(content) / (1024 * 1024),
        thumbnail_url=f"/api/assets/avatars/{file_id}/thumbnail",
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    
    logger.info(f"Avatar uploaded: {asset.id}")
    return asset


@router.get("/avatars", response_model=AssetListResponse)
async def list_avatars(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """List all avatars"""
    result = await db.execute(
        select(Asset)
        .where(Asset.asset_type == AssetType.AVATAR)
        .offset(skip)
        .limit(limit)
    )
    assets = result.scalars().all()
    
    count_result = await db.execute(
        select(Asset).where(Asset.asset_type == AssetType.AVATAR)
    )
    total = len(count_result.scalars().all())
    
    return {"assets": assets, "total": total}


@router.delete("/avatars/{asset_id}")
async def delete_avatar(asset_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an avatar"""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found",
        )
    
    # Delete file
    try:
        Path(asset.file_path).unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
    
    await db.delete(asset)
    await db.commit()
    
    return {"ok": True}
