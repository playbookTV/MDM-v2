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
from app.services.huggingface import HuggingFaceService
from app.services.roboflow import RoboflowService
from app.schemas.database import Dataset, DatasetCreate, SceneCreate
from app.core.config import settings
from app.core.validation import validate_huggingface_url

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

class ProcessHuggingFaceRequest(BaseModel):
    """Process HuggingFace dataset request"""
    hf_url: str
    split: str = "train"
    image_column: str = "image"
    max_images: Optional[int] = None

class ProcessHuggingFaceResponse(BaseModel):
    """Process HuggingFace dataset response"""
    job_id: str
    status: str

class ProcessRoboflowRequest(BaseModel):
    """Process Roboflow dataset request"""
    roboflow_url: str
    api_key: Optional[str] = None  # Optional, will use env var if not provided
    export_format: str = "coco"
    max_images: Optional[int] = None

class ProcessRoboflowResponse(BaseModel):
    """Process Roboflow dataset response"""
    job_id: str
    status: str

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

@router.post("/{dataset_id}/process-huggingface", response_model=ProcessHuggingFaceResponse)
async def process_huggingface_dataset(
    dataset_id: str,
    request: ProcessHuggingFaceRequest
):
    """Process HuggingFace dataset: validate URL and start background job"""
    try:
        # Verify dataset exists
        service = DatasetService()
        dataset = await service.get_dataset(dataset_id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Validate HuggingFace URL (security + format)
        validate_huggingface_url(request.hf_url)
        
        # Additional validation with HuggingFace service
        hf_service = HuggingFaceService()
        org_dataset = hf_service.validate_hf_url(request.hf_url)
        
        if not org_dataset:
            raise HTTPException(
                status_code=400, 
                detail="Invalid HuggingFace dataset URL or dataset not accessible"
            )
        
        # Import the task here to avoid circular imports
        from app.worker.huggingface_tasks import process_huggingface_dataset as hf_task
        
        # Start background processing job
        job = hf_task.delay(
            dataset_id=dataset_id,
            hf_dataset_url=request.hf_url,
            split=request.split,
            image_column=request.image_column,
            max_images=request.max_images
        )
        
        logger.info(f"Started HF processing job {job.id} for dataset {dataset_id}")
        
        return ProcessHuggingFaceResponse(
            job_id=str(job.id),
            status="started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start HF processing for dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start HuggingFace processing")

@router.post("/{dataset_id}/process-roboflow", response_model=ProcessRoboflowResponse)
async def process_roboflow_dataset(
    dataset_id: str,
    request: ProcessRoboflowRequest
):
    """Process Roboflow dataset: validate URL and start background job"""
    try:
        # Verify dataset exists
        service = DatasetService()
        dataset = await service.get_dataset(dataset_id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Validate Roboflow URL format
        roboflow_service = RoboflowService()
        url_parts = roboflow_service.validate_roboflow_url(request.roboflow_url)
        
        if not url_parts:
            raise HTTPException(
                status_code=400, 
                detail="Invalid Roboflow Universe URL format. Expected: https://universe.roboflow.com/workspace/project/model/version"
            )
        
        # Use environment variable if API key not provided
        api_key = request.api_key or settings.ROBOFLOW_API_KEY
        
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="Roboflow API key required. Please provide api_key or set ROBOFLOW_API_KEY environment variable"
            )
        
        # Additional validation with Roboflow service (check API key and dataset access)
        dataset_info = roboflow_service.extract_dataset_info(request.roboflow_url, api_key)
        
        if not dataset_info:
            raise HTTPException(
                status_code=400, 
                detail="Invalid Roboflow dataset URL, inaccessible dataset, or invalid API key"
            )
        
        # Import the task here to avoid circular imports
        from app.worker.roboflow_tasks import process_roboflow_dataset as rf_task
        
        # Start background processing job
        job = rf_task.delay(
            dataset_id=dataset_id,
            roboflow_dataset_url=request.roboflow_url,
            api_key=api_key,
            export_format=request.export_format,
            max_images=request.max_images
        )
        
        logger.info(f"Started Roboflow processing job {job.id} for dataset {dataset_id}")
        
        return ProcessRoboflowResponse(
            job_id=str(job.id),
            status="started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start Roboflow processing for dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start Roboflow processing")

@router.post("/{dataset_id}/process-ai")
async def trigger_ai_processing(dataset_id: str):
    """Trigger AI processing for existing scenes in a dataset"""
    try:
        # Verify dataset exists
        service = DatasetService()
        dataset = await service.get_dataset(dataset_id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Check if dataset has scenes to process
        from app.services.scenes import SceneService
        scene_service = SceneService()
        scenes = await scene_service.get_scenes(dataset_id=dataset_id, limit=1)
        
        if not scenes or len(scenes.get('items', [])) == 0:
            raise HTTPException(
                status_code=400, 
                detail="No scenes found in dataset. Import scenes first using /process-huggingface endpoint."
            )
        
        # Import the task to start AI processing
        from app.worker.tasks import process_scenes_in_dataset
        from app.services.jobs import JobService
        
        # Create a job record for tracking
        job_service = JobService()
        job = await job_service.create_job(
            type="ai_processing",
            dataset_id=dataset_id,
            params={"trigger": "manual"}
        )
        
        # Start AI processing task
        task = process_scenes_in_dataset.delay(
            job_id=str(job.id),
            dataset_id=dataset_id,
            options={"trigger": "manual"}
        )
        
        logger.info(f"Started AI processing job {job.id} for dataset {dataset_id}")
        
        return {
            "job_id": str(job.id),
            "task_id": str(task.id),
            "status": "started",
            "message": "AI processing started for dataset"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start AI processing for dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start AI processing")