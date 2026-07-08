"""
Project management endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import Project
from schemas import ProjectCreate, ProjectUpdate, ProjectResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    user_id: str = "demo-user",  # Would come from JWT
    db: AsyncSession = Depends(get_db),
):
    """Create a new project"""
    project = Project(
        user_id=user_id,
        name=project_data.name,
        description=project_data.description,
        is_public=project_data.is_public,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    logger.info(f"Project created: {project.id}")
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get project details"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    if project_data.name:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.is_public is not None:
        project.is_public = project_data.is_public
    
    await db.commit()
    await db.refresh(project)
    
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Delete project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    await db.delete(project)
    await db.commit()
    
    return {"ok": True}
