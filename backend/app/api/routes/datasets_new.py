"""
Dataset management endpoints using Supabase
"""

import uuid
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.datasets import DatasetService
from app.services.storage import StorageService
from app.schemas.database import Dataset, DatasetCreate, SceneCreate
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response schemas
class PresignFileRequest(BaseModel):
    """Single file presign request"""
    filename: str
    content_type: str

class PresignRequest(BaseModel):
    """Presigned URLs request"""
    files: List[PresignFileRequest]

class PresignUpload(BaseModel):
    """Single presigned upload response"""
    filename: str
    key: str
    url: str
    headers: dict

class PresignResponse(BaseModel):
    """Presigned URLs response"""
    uploads: List[PresignUpload]

class RegisterScenesRequest(BaseModel):
    """Register scenes request"""
    scenes: List[SceneCreate]

class RegisterScenesResponse(BaseModel):
    """Register scenes response"""
    created: int
    scene_ids: List[str]

@router.get("")
async def get_datasets(
    q: Optional[str] = Query(None, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE, description="Items per page")
):
    """Get paginated list of datasets with optional search"""
    try:
        service = DatasetService()
        result = await service.get_datasets(
            page=page,
            per_page=limit,
            search=q
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
        logger.error(f"Failed to fetch datasets: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch datasets")

@router.post("", response_model=Dataset)
async def create_dataset(dataset_data: DatasetCreate):
    """Create a new dataset"""
    try:
        service = DatasetService()
        dataset = await service.create_dataset(dataset_data)
        
        logger.info(f"Created dataset: {dataset.id} ({dataset.name})")
        return dataset
        
    except Exception as e:
        logger.error(f"Failed to create dataset: {e}")
        raise HTTPException(status_code=500, detail="Failed to create dataset")

@router.get("/{dataset_id}", response_model=Dataset)
async def get_dataset(dataset_id: str):
    """Get dataset by ID"""
    try:
        service = DatasetService()
        dataset = await service.get_dataset(dataset_id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        return dataset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dataset")

@router.post("/{dataset_id}/presign", response_model=PresignResponse)
async def get_presigned_urls(
    dataset_id: str,
    request: PresignRequest
):
    """Get presigned URLs for uploading files to R2 storage"""
    try:
        # Verify dataset exists
        service = DatasetService()
        dataset = await service.get_dataset(dataset_id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Generate presigned URLs
        storage = StorageService()
        uploads = []
        
        for file_req in request.files:
            # Validate file type
            if file_req.content_type not in settings.ALLOWED_IMAGE_TYPES:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file_req.content_type}"
                )
            
            # Generate R2 key
            file_id = str(uuid.uuid4())
            file_ext = file_req.filename.split('.')[-1].lower()
            r2_key = f"scenes/{file_id}.{file_ext}"
            
            # Generate presigned URL
            presigned_url, headers = await storage.generate_presigned_upload_url(
                key=r2_key,
                content_type=file_req.content_type,
                expires_in=settings.PRESIGNED_URL_EXPIRES
            )
            
            uploads.append(PresignUpload(
                filename=file_req.filename,
                key=r2_key,
                url=presigned_url,
                headers=headers
            ))
        
        logger.info(f"Generated {len(uploads)} presigned URLs for dataset {dataset_id}")
        return PresignResponse(uploads=uploads)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate presigned URLs for dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate presigned URLs")

@router.post("/{dataset_id}/register-scenes", response_model=RegisterScenesResponse)
async def register_scenes(
    dataset_id: str,
    request: RegisterScenesRequest
):
    """Register uploaded files as scenes in the dataset"""
    try:
        # Verify dataset exists
        service = DatasetService()
        dataset = await service.get_dataset(dataset_id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Set dataset_id for all scenes
        for scene_data in request.scenes:
            scene_data.dataset_id = dataset_id
        
        # Create scene records
        created_scenes = await service.create_scenes_batch(request.scenes)
        scene_ids = [scene.id for scene in created_scenes]
        
        logger.info(f"Registered {len(scene_ids)} scenes for dataset {dataset_id}")
        return RegisterScenesResponse(
            created=len(scene_ids),
            scene_ids=scene_ids
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register scenes for dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to register scenes")

@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """Delete a dataset and all associated scenes"""
    try:
        service = DatasetService()
        success = await service.delete_dataset(dataset_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # TODO: Delete associated R2 objects
        # For now, we'll just delete the database records
        # In production, should clean up R2 storage as well
        
        logger.info(f"Deleted dataset {dataset_id}")
        return {"message": "Dataset deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete dataset")