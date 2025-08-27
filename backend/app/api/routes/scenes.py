"""
Scene management endpoints
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.dataset import Scene, SceneObject, Dataset
from app.schemas.dataset import (
    Scene as SceneSchema,
    SceneObject as SceneObjectSchema
)
from app.schemas.common import Page
from app.services.storage import StorageService
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("", response_model=Page[SceneSchema])
async def get_scenes(
    db: AsyncSession = Depends(get_db),
    dataset_id: Optional[str] = Query(None, description="Filter by dataset"),
    review_status: Optional[str] = Query(None, description="Filter by review status"),
    scene_type: Optional[str] = Query(None, description="Filter by scene type"),
    include_objects: bool = Query(False, description="Include detected objects"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE, description="Items per page")
):
    """Get paginated list of scenes with optional filters"""
    try:
        offset = (page - 1) * limit
        
        # Build query with optional joins
        if include_objects:
            query = select(Scene).options(selectinload(Scene.objects))
        else:
            query = select(Scene)
        
        # Include dataset name
        query = query.join(Dataset).add_columns(Dataset.name.label('dataset_name'))
        
        count_query = select(func.count(Scene.id))
        
        # Apply filters
        filters = []
        if dataset_id:
            filters.append(Scene.dataset_id == dataset_id)
        if review_status:
            filters.append(Scene.review_status == review_status)
        if scene_type:
            filters.append(Scene.scene_type == scene_type)
        
        if filters:
            combined_filter = and_(*filters)
            query = query.where(combined_filter)
            count_query = count_query.where(combined_filter)
        
        # Order by creation time
        query = query.order_by(desc(Scene.created_at))
        
        # Execute queries
        total = await db.scalar(count_query)
        result = await db.execute(query.offset(offset).limit(limit))
        
        # Process results to add dataset names
        scenes = []
        for row in result:
            scene = row.Scene
            # Add dataset name to scene
            scene.dataset_name = row.dataset_name
            scenes.append(scene)
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        
        return Page(
            items=scenes,
            total=total,
            page=page,
            limit=limit,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch scenes: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scenes")

@router.get("/{scene_id}", response_model=SceneSchema)
async def get_scene(
    scene_id: str,
    db: AsyncSession = Depends(get_db),
    include_objects: bool = Query(True, description="Include detected objects")
):
    """Get scene by ID with optional objects"""
    try:
        # Build query
        query = select(Scene).where(Scene.id == scene_id)
        
        if include_objects:
            query = query.options(selectinload(Scene.objects))
        
        # Join with dataset for name
        query = query.join(Dataset).add_columns(Dataset.name.label('dataset_name'))
        
        result = await db.execute(query)
        row = result.first()
        
        if not row:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        scene = row.Scene
        scene.dataset_name = row.dataset_name
        
        return scene
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scene")

@router.get("/{scene_id}/objects", response_model=List[SceneObjectSchema])
async def get_scene_objects(
    scene_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all objects detected in a scene"""
    try:
        # Verify scene exists
        scene_query = select(Scene).where(Scene.id == scene_id)
        scene_result = await db.execute(scene_query)
        scene = scene_result.scalar_one_or_none()
        
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        # Get objects
        query = select(SceneObject).where(SceneObject.scene_id == scene_id)
        result = await db.execute(query)
        objects = result.scalars().all()
        
        return objects
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch objects for scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scene objects")

@router.get("/{scene_id}/image-url")
async def get_scene_image_url(
    scene_id: str,
    db: AsyncSession = Depends(get_db),
    image_type: str = Query("original", description="Image type: original, thumbnail, depth")
):
    """Get presigned URL for viewing scene images"""
    try:
        query = select(Scene).where(Scene.id == scene_id)
        result = await db.execute(query)
        scene = result.scalar_one_or_none()
        
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        # Get appropriate R2 key
        r2_key = None
        if image_type == "original":
            r2_key = scene.r2_key_original
        elif image_type == "thumbnail":
            r2_key = scene.r2_key_thumbnail
        elif image_type == "depth":
            r2_key = scene.r2_key_depth
        else:
            raise HTTPException(status_code=400, detail="Invalid image type")
        
        if not r2_key:
            raise HTTPException(status_code=404, detail=f"No {image_type} image available")
        
        # Generate presigned URL
        storage = StorageService()
        url = await storage.generate_presigned_download_url(r2_key, expires_in=3600)
        
        return {"url": url, "expires_in": 3600}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get image URL for scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get image URL")

@router.patch("/{scene_id}")
async def update_scene(
    scene_id: str,
    updates: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update scene metadata (for corrections/reviews)"""
    try:
        query = select(Scene).where(Scene.id == scene_id)
        result = await db.execute(query)
        scene = result.scalar_one_or_none()
        
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        # Apply allowed updates
        allowed_fields = [
            'scene_type', 'review_status', 'review_notes', 'reviewed_by', 'styles'
        ]
        
        updated = False
        for field, value in updates.items():
            if field in allowed_fields and hasattr(scene, field):
                setattr(scene, field, value)
                updated = True
        
        if updated:
            await db.commit()
            await db.refresh(scene)
        
        return {"message": "Scene updated successfully", "updated": updated}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update scene {scene_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update scene")

@router.patch("/{scene_id}/objects/{object_id}")
async def update_scene_object(
    scene_id: str,
    object_id: str,
    updates: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update scene object metadata (for corrections/reviews)"""
    try:
        query = select(SceneObject).where(
            SceneObject.id == object_id,
            SceneObject.scene_id == scene_id
        )
        result = await db.execute(query)
        obj = result.scalar_one_or_none()
        
        if not obj:
            raise HTTPException(status_code=404, detail="Object not found")
        
        # Apply allowed updates
        allowed_fields = [
            'label', 'material', 'review_status', 'review_notes'
        ]
        
        updated = False
        for field, value in updates.items():
            if field in allowed_fields and hasattr(obj, field):
                setattr(obj, field, value)
                updated = True
        
        if updated:
            await db.commit()
            await db.refresh(obj)
        
        return {"message": "Object updated successfully", "updated": updated}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update object {object_id} in scene {scene_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update object")