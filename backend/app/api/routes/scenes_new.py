"""
Scene management endpoints using Supabase
"""

import uuid
import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services.scenes import SceneService
from app.services.jobs import JobService
from app.schemas.database import Scene, SceneObject, JobCreate
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class ProcessSceneRequest(BaseModel):
    """Request body for scene processing"""
    force_reprocess: Optional[bool] = False

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
        scene_data = await service.get_scene(scene_id, include_objects=include_objects)
        
        if not scene_data:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        return scene_data
        
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
        objects = await service.get_scene_objects(scene_id)
        return objects
        
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
        # Validate image type
        if image_type not in ["original", "depth"]:
            raise HTTPException(status_code=400, detail="Invalid image type")
        
        service = SceneService()
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
        success = await service.update_scene_object(scene_id, object_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="Object not found")
        
        return {"message": "Object updated successfully", "updated": success}
        
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
    request: ProcessSceneRequest = None,
    force_reprocess: bool = Query(False, description="Force reprocessing even if already processed")
):
    """Trigger AI processing for a specific scene"""
    try:
        service = SceneService()
        job_service = JobService()
        
        # Check if scene exists
        scene_data = await service.get_scene(scene_id, include_objects=False)
        if not scene_data:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        # Determine force_reprocess from request body or query param
        should_force_reprocess = force_reprocess
        if request and request.force_reprocess is not None:
            should_force_reprocess = request.force_reprocess
        
        # Check if already processed (unless forcing)
        if not should_force_reprocess and scene_data.get("status") == "processed":
            return {
                "message": "Scene already processed",
                "scene_id": scene_id,
                "status": "skipped",
                "job_id": None
            }
        
        # Create a real processing job
        job_data = JobCreate(
            kind="process",
            dataset_id=scene_data.get("dataset_id"),
            meta={
                "scene_id": scene_id,
                "force_reprocess": should_force_reprocess,
                "processing_type": "ai_pipeline"
            }
        )
        
        job = await job_service.create_job(job_data)
        job_id = str(job.id)
        
        logger.info(f"Created scene processing job {job_id} for scene {scene_id}")
        
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
        scene_data = await service.get_scene(scene_id, include_objects=False)
        if not scene_data:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        scene_status = scene_data.get("status", "unprocessed")
        
        # Simple status mapping based on scene status
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
        elif scene_status == "processing":
            return {
                "scene_id": scene_id,
                "job_id": None,
                "status": "running",
                "progress": 50,
                "stage": "processing",
                "description": "AI analysis in progress...",
                "started_at": None,
                "finished_at": None,
                "error": None
            }
        elif scene_status == "failed":
            return {
                "scene_id": scene_id,
                "job_id": None,
                "status": "failed",
                "progress": 0,
                "stage": "failed",
                "description": "Scene processing failed",
                "started_at": None,
                "finished_at": None,
                "error": "Processing failed"
            }
        else:
            return {
                "scene_id": scene_id,
                "job_id": None,
                "status": "no_job",
                "progress": 0,
                "stage": "idle",
                "description": "Scene not processed yet",
                "started_at": None,
                "finished_at": None,
                "error": None
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processing status for scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing status")
