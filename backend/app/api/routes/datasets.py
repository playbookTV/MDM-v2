"""
Dataset management endpoints
"""

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.dataset import Dataset, Scene
from app.schemas.dataset import (
    Dataset as DatasetSchema,
    DatasetCreate,
    PresignRequest,
    PresignResponse,
    PresignUpload,
    RegisterScenesRequest,
    RegisterScenesResponse
)
from app.schemas.common import Page
from app.services.storage import StorageService
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=Page[DatasetSchema])
async def get_datasets(
    db: AsyncSession = Depends(get_db),
    q: Optional[str] = Query(None, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(
        20, ge=1, le=settings.MAX_PAGE_SIZE, description="Items per page"
    )
):
    """Get paginated list of datasets with optional search"""
    try:
        offset = (page - 1) * limit
        
        # Build query
        query = select(Dataset).order_by(desc(Dataset.created_at))
        count_query = select(func.count(Dataset.id))
        
        if q:
            search_filter = Dataset.name.ilike(f"%{q}%") | Dataset.description.ilike(f"%{q}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Execute queries
        total = await db.scalar(count_query)
        result = await db.execute(query.offset(offset).limit(limit))
        datasets = result.scalars().all()
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        
        return Page(
            items=datasets,
            total=total,
            page=page,
            limit=limit,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch datasets: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch datasets")

@router.post("", response_model=DatasetSchema)
async def create_dataset(
    dataset_data: DatasetCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new dataset"""
    try:
        # Create dataset record
        dataset = Dataset(
            id=str(uuid.uuid4()),
            name=dataset_data.name,
            description=dataset_data.description,
            source=dataset_data.source,
            source_url=dataset_data.source_url,
            tags=dataset_data.tags,
            attrs={},
            total_scenes=0,
            processed_scenes=0,
            total_objects=0,
        )
        
        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)
        
        logger.info(f"Created dataset: {dataset.id} ({dataset.name})")
        return dataset
        
    except Exception as e:
        logger.error(f"Failed to create dataset: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create dataset")

@router.get("/{dataset_id}", response_model=DatasetSchema)
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get dataset by ID"""
    try:
        query = select(Dataset).where(Dataset.id == dataset_id)
        result = await db.execute(query)
        dataset = result.scalar_one_or_none()
        
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
    request: PresignRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get presigned URLs for uploading files to R2 storage"""
    try:
        # Verify dataset exists
        query = select(Dataset).where(Dataset.id == dataset_id)
        result = await db.execute(query)
        dataset = result.scalar_one_or_none()
        
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
    request: RegisterScenesRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register uploaded files as scenes in the dataset"""
    try:
        # Verify dataset exists
        query = select(Dataset).where(Dataset.id == dataset_id)
        result = await db.execute(query)
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Create scene records
        scene_ids = []
        created_scenes = []
        
        for scene_data in request.scenes:
            scene = Scene(
                id=str(uuid.uuid4()),
                dataset_id=dataset_id,
                source=scene_data.source,
                r2_key_original=scene_data.r2_key_original,
                width=scene_data.width,
                height=scene_data.height,
                status="pending",
                styles=[],
                palette=[],
                attrs={}
            )
            
            created_scenes.append(scene)
            scene_ids.append(scene.id)
            db.add(scene)
        
        # Update dataset stats
        dataset.total_scenes += len(created_scenes)
        
        await db.commit()
        
        # Refresh scenes to get timestamps
        for scene in created_scenes:
            await db.refresh(scene)
        
        logger.info(f"Registered {len(scene_ids)} scenes for dataset {dataset_id}")
        return RegisterScenesResponse(
            created=len(scene_ids),
            scene_ids=scene_ids
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register scenes for dataset {dataset_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to register scenes")

@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a dataset and all associated scenes"""
    try:
        # Get dataset with scenes
        query = select(Dataset).where(Dataset.id == dataset_id).options(
            selectinload(Dataset.scenes)
        )
        result = await db.execute(query)
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # TODO: Delete associated R2 objects
        # For now, we'll just delete the database records
        # In production, should clean up R2 storage as well
        
        await db.delete(dataset)
        await db.commit()
        
        logger.info(f"Deleted dataset {dataset_id} with {len(dataset.scenes)} scenes")
        return {"message": "Dataset deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dataset {dataset_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete dataset")