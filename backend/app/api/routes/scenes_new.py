"""
Scene management endpoints using Supabase
"""

import uuid
import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.scenes import SceneService
from app.schemas.database import Scene, SceneObject
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("")
async def get_scenes(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset"),
    review_status: Optional[str] = Query(None, description="Filter by review status"),
    scene_type: Optional[str] = Query(None, description="Filter by scene type"),
    include_objects: bool = Query(False, description="Include detected objects"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE, description="Items per page")
):
    """Get paginated list of scenes with optional filters"""
    try:
        service = SceneService()
        result = await service.get_scenes(
            page=page,
            per_page=limit,
            dataset_id=dataset_id,
            review_status=review_status,
            scene_type=scene_type,
            include_objects=include_objects
        )
        
        return {
            "items": result["data"],
            "total": result["total_count"],
            "page": page,
            "limit": limit,
            "pages": result["total_pages"],
            "has_next": page < result["total_pages"],
            "has_prev": page > 1
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch scenes: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scenes")

@router.get("/{scene_id}")
async def get_scene(
    scene_id: str,
    include_objects: bool = Query(True, description="Include detected objects")
):
    """Get scene by ID with optional objects"""
    try:
        service = SceneService()
        scene = await service.get_scene(scene_id, include_objects)
        
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        return scene
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scene")

@router.get("/{scene_id}/objects")
async def get_scene_objects(scene_id: str):
    """Get all objects detected in a scene"""
    try:
        service = SceneService()
        
        # First verify scene exists
        scene = await service.get_scene(scene_id, include_objects=False)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        # Get objects
        objects = await service.get_scene_objects(scene_id)
        return [obj.model_dump() for obj in objects]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch objects for scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scene objects")

@router.get("/{scene_id}/image-url")
async def get_scene_image_url(
    scene_id: str,
    image_type: str = Query("original", description="Image type: original, depth")
):
    """Get presigned URL for viewing scene images"""
    try:
        service = SceneService()
        
        # Validate image type
        if image_type not in ["original", "depth"]:
            raise HTTPException(status_code=400, detail="Invalid image type")
        
        url = await service.get_scene_image_url(scene_id, image_type)
        
        if not url:
            if image_type == "original":
                raise HTTPException(status_code=404, detail="Scene not found")
            else:
                raise HTTPException(status_code=404, detail=f"No {image_type} image available")
        
        return {"url": url, "expires_in": 3600}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get image URL for scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get image URL")

@router.patch("/{scene_id}")
async def update_scene(scene_id: str, updates: dict):
    """Update scene metadata (for corrections/reviews)"""
    try:
        service = SceneService()
        
        # Verify scene exists
        scene = await service.get_scene(scene_id, include_objects=False)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        # Update scene
        success = await service.update_scene(scene_id, updates)
        
        return {"message": "Scene updated successfully", "updated": success}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update scene")

@router.patch("/{scene_id}/objects/{object_id}")
async def update_scene_object(
    scene_id: str,
    object_id: str,
    updates: dict
):
    """Update scene object metadata (for corrections/reviews)"""
    try:
        service = SceneService()
        
        # Update object
        success = await service.update_scene_object(scene_id, object_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="Object not found")
        
        return {"message": "Object updated successfully", "updated": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update object {object_id} in scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update object")

# Additional endpoint for React hook compatibility
@router.get("/paginated/list")
async def get_scenes_paginated(
    dataset_id: Optional[str] = Query(None),
    review_status: Optional[str] = Query(None),
    scene_type: Optional[str] = Query(None),
    limit: int = Query(50, le=100)
):
    """Get scenes in format compatible with useScenePagination hook"""
    try:
        service = SceneService()
        result = await service.get_scenes_paginated(
            dataset_id=dataset_id,
            review_status=review_status,
            scene_type=scene_type,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to fetch paginated scenes: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scenes")

@router.post("/{scene_id}/process")
async def process_scene_endpoint(
    scene_id: str,
    force_reprocess: bool = Query(False, description="Force reprocessing even if already processed")
):
    """Trigger AI processing for a specific scene"""
    try:
        service = SceneService()
        
        # Check if scene exists
        scene = await service.get_scene(scene_id, include_objects=False)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        # Check if already processed (unless forcing)
        if not force_reprocess and scene.get("status") == "processed":
            return {
                "message": "Scene already processed",
                "scene_id": scene_id,
                "status": "skipped",
                "job_id": None
            }
        
        # For now, return a mock processing response
        # In production, this would create a real processing job
        job_id = str(uuid.uuid4())
        
        logger.info(f"Mock scene processing job {job_id} for scene {scene_id}")
        
        return {
            "message": "Scene processing started",
            "scene_id": scene_id,
            "job_id": job_id,
            "status": "queued"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start scene processing for {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start scene processing")

@router.get("/{scene_id}/process-status")
async def get_scene_process_status(scene_id: str):
    """Get the current processing status for a scene"""
    try:
        service = SceneService()
        
        # Check if scene exists
        scene = await service.get_scene(scene_id, include_objects=False)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        # For now, return mock status based on scene data
        # In production, this would check actual job status
        scene_status = scene.get("status", "unprocessed")
        
        if scene_status == "processed":
            return {
                "scene_id": scene_id,
                "job_id": None,
                "status": "succeeded",
                "progress": 100,
                "stage": "completed",
                "description": "Scene processing completed successfully",
                "started_at": None,
                "finished_at": None,
                "error": None
            }
        else:
            return {
                "scene_id": scene_id,
                "job_id": None,
                "status": "no_job",
                "progress": 0,
                "stage": "idle",
                "description": "No processing job found for this scene",
                "started_at": None,
                "finished_at": None,
                "error": None
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processing status for scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing status")