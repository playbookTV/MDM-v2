"""
Celery tasks for HuggingFace dataset processing
"""

import logging
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime, timezone
import traceback
from uuid import uuid4

from celery import current_task
from app.worker.celery_app import celery_app
from app.services.huggingface import HuggingFaceService
from app.services.datasets import DatasetService
from app.services.jobs import JobService
from app.schemas.dataset import SceneCreate
from app.core.config import settings
from app.core.supabase import init_supabase
from app.core.redis import init_redis

logger = logging.getLogger(__name__)


async def _find_or_create_job_record(dataset_id: str, hf_url: str, celery_task_id: str) -> str:
    """Find existing job or link to existing queued job"""
    try:
        from app.core.supabase import get_supabase
        
        supabase = get_supabase()
        
        # First, try to find a queued job for this dataset - this is likely the job from the UI
        result = supabase.table("jobs").select("*").eq(
            "dataset_id", dataset_id
        ).eq("status", "queued").order("created_at", desc=True).limit(1).execute()
        
        if result.data:
            job_id = result.data[0]["id"]
            # Update the job with our Celery task ID for tracking
            supabase.table("jobs").update({
                "meta": {
                    "celery_task_id": celery_task_id,
                    "hf_url": hf_url,
                    "processing_type": "huggingface"
                }
            }).eq("id", job_id).execute()
            
            logger.info(f"Linked to existing job {job_id} for Celery task {celery_task_id}")
            return job_id
        
        # Fallback: create new job if no queued job found
        job_id = str(uuid4())
        job_data = {
            "id": job_id,
            "kind": "ingest", 
            "status": "queued",
            "dataset_id": dataset_id,
            "meta": {
                "celery_task_id": celery_task_id,
                "hf_url": hf_url,
                "processing_type": "huggingface"
            },
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        supabase.table("jobs").insert(job_data).execute()
        logger.info(f"Created new job record {job_id} for Celery task {celery_task_id}")
        return job_id
        
    except Exception as e:
        logger.error(f"Failed to find/create job record: {e}")
        return str(uuid4())  # Fallback to random ID


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_huggingface_dataset(
    self,
    dataset_id: str,
    hf_dataset_url: str,
    subset: Optional[str] = None,
    split: str = "train",
    image_column: str = "image",
    max_images: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process HuggingFace dataset: download images and create scene records.
    
    Args:
        dataset_id: Supabase dataset ID
        hf_dataset_url: HuggingFace dataset URL
        subset: Dataset subset (if applicable)
        split: Dataset split to process
        image_column: Column containing images
        max_images: Maximum images to process
        
    Returns:
        Processing results dictionary
        
    Example:
        >>> result = process_huggingface_dataset.delay(
        ...     "dataset-123",
        ...     "https://huggingface.co/datasets/nlphuji/flickr30k"
        ... )
        >>> result.get()
        {"status": "completed", "processed_scenes": 150, "failed_scenes": 5}
    """
    job_id = None
    job_service = None
    
    async def _async_wrapper():
        nonlocal job_id, job_service
        
        # Initialize async services
        await init_supabase()
        await init_redis()
        job_service = JobService()
        
        # Find or create job record for this Celery task
        job_id = await _find_or_create_job_record(
            dataset_id, hf_dataset_url, self.request.id
        )
        
        logger.info(
            f"Starting HF dataset processing",
            extra={
                "celery_task_id": self.request.id,
                "job_id": job_id,
                "dataset_id": dataset_id,
                "hf_url": hf_dataset_url,
                "max_images": max_images
            }
        )
        
        return job_id, job_service
    
    try:
        # Run async initialization
        job_id, job_service = asyncio.run(_async_wrapper())
        
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'status': 'initializing', 'processed': 0, 'total': 0, 'job_id': job_id}
        )
        
        # Update job status to running
        if job_service:
            asyncio.run(job_service.update_job(job_id, {
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat()
            }))
        
        # Initialize services
        hf_service = HuggingFaceService()
        dataset_service = DatasetService()
        
        # Validate dataset exists - using sync version for Celery
        try:
            dataset = dataset_service.get_dataset_sync(dataset_id)
            if not dataset:
                logger.error(f"Dataset {dataset_id} not found")
                return {"status": "failed", "error": "Dataset not found"}
        except Exception as e:
            logger.error(f"Failed to validate dataset {dataset_id}: {e}")
            return {"status": "failed", "error": f"Dataset validation failed: {e}"}
        
        # Load images from HuggingFace
        self.update_state(
            state='PROGRESS',
            meta={'status': 'loading_hf_dataset', 'processed': 0, 'total': 0}
        )
        
        images = hf_service.load_hf_dataset_images(
            hf_url=hf_dataset_url,
            split=split,
            image_column=image_column,
            max_images=max_images
        )
        
        if not images:
            logger.error(f"No images loaded from HF dataset: {hf_dataset_url}")
            return {"status": "failed", "error": "No images found in dataset"}
        
        total_images = len(images)
        logger.info(f"Loaded {total_images} images from HF dataset")
        
        # Process images
        processed_scenes = []
        failed_scenes = 0
        
        for idx, image_data in enumerate(images):
            try:
                # Update progress
                if idx % 10 == 0:
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'status': 'processing_images',
                            'processed': idx,
                            'total': total_images,
                            'current_image': f"hf_image_{image_data['hf_index']}"
                        }
                    )
                
                # Upload image to R2 - using sync version for Celery
                filename = f"hf_image_{image_data['hf_index']}.jpg"
                r2_key = hf_service.upload_image_to_r2_sync(
                    image_data['image'], 
                    filename
                )
                
                if not r2_key:
                    logger.warning(f"Failed to upload image {idx} to R2")
                    failed_scenes += 1
                    continue
                
                # Create scene record - using sync version for Celery
                scene_data = SceneCreate(
                    source=f"huggingface:{hf_dataset_url}",
                    r2_key_original=r2_key,
                    width=image_data['width'],
                    height=image_data['height']
                )
                
                scene = dataset_service.create_scene_sync(dataset_id, scene_data)
                processed_scenes.append(scene.id)
                
                logger.debug(f"Processed image {idx + 1}/{total_images}: {scene.id}")
                
            except Exception as e:
                logger.error(f"Failed to process image {idx}: {e}")
                failed_scenes += 1
                continue
        
        # Final status update - match specification contract
        result = {
            "status": "completed",
            "processed_scenes": len(processed_scenes),
            "failed_scenes": failed_scenes,
            "job_id": job_id
        }
        
        # Update job status to completed
        if job_service:
            asyncio.run(job_service.update_job(job_id, {
                "status": "succeeded",
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "meta": {
                    **result,
                    "celery_task_id": self.request.id,
                    "hf_url": hf_dataset_url
                }
            }))
        
        logger.info(
            f"HF dataset processing completed",
            extra={
                "job_id": job_id,
                "dataset_id": dataset_id,
                "processed_scenes": len(processed_scenes),
                "failed_scenes": failed_scenes,
                "total_images": total_images
            }
        )
        
        # AUTO-TRIGGER AI PROCESSING: Start AI processing for all scenes after successful ingestion
        if len(processed_scenes) > 0:
            logger.info(f"Auto-triggering AI processing for {len(processed_scenes)} scenes in dataset {dataset_id}")
            
            # Import here to avoid circular imports
            from app.worker.tasks import process_scenes_in_dataset
            
            # Trigger AI processing job for the dataset
            ai_job_id = str(uuid4())
            ai_processing_task = process_scenes_in_dataset.delay(
                ai_job_id,
                dataset_id,
                {
                    "trigger": "auto_after_ingestion",
                    "source_job": job_id,
                    "scene_ids": processed_scenes
                }
            )
            
            logger.info(f"Started AI processing job {ai_job_id} with Celery task {ai_processing_task.id}")
            
            # Create job record for AI processing directly in Supabase
            if job_service:
                from app.core.supabase import get_supabase
                supabase = get_supabase()
                
                job_data = {
                    "id": ai_job_id,
                    "dataset_id": dataset_id,
                    "kind": "ai_processing",
                    "status": "queued",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "meta": {
                        "celery_task_id": ai_processing_task.id,
                        "trigger": "auto_after_ingestion",
                        "source_job": job_id,
                        "total_scenes": len(processed_scenes)
                    }
                }
                
                supabase.table("jobs").insert(job_data).execute()
                logger.info(f"Created AI processing job record {ai_job_id}")
                
        else:
            logger.warning("No scenes processed successfully - skipping AI processing trigger")
        
        self.update_state(
            state='SUCCESS',
            meta=result
        )
        
        return result
        
    except Exception as e:
        error_message = str(e)
        error_traceback = traceback.format_exc()
        
        logger.error(
            f"HF dataset processing failed: {error_message}",
            extra={
                "job_id": job_id,
                "dataset_id": dataset_id,
                "hf_url": hf_dataset_url,
                "celery_task_id": self.request.id,
                "retry_count": self.request.retries,
                "traceback": error_traceback
            }
        )
        
        # Update job status to failed
        if job_service:
            try:
                asyncio.run(job_service.update_job(job_id, {
                    "status": "failed",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "error": error_message,
                    "meta": {
                        "celery_task_id": self.request.id,
                        "hf_url": hf_dataset_url,
                        "retry_count": self.request.retries,
                        "error_type": type(e).__name__
                    }
                }))
            except Exception as update_error:
                logger.error(f"Failed to update job status: {update_error}")
        
        # Retry on certain errors (but not validation errors)
        if (self.request.retries < self.max_retries and 
            not isinstance(e, (ValueError, FileNotFoundError)) and
            "not found" not in error_message.lower()):
            logger.info(f"Retrying HF processing (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        error_result = {
            "status": "failed",
            "error": error_message,
            "processed_scenes": 0,
            "failed_scenes": 0,
            "job_id": job_id
        }
        
        self.update_state(
            state='FAILURE',
            meta=error_result
        )
        
        return error_result

@celery_app.task
def validate_huggingface_url(hf_url: str) -> Dict[str, Any]:
    """
    Validate HuggingFace dataset URL and extract metadata.
    
    Args:
        hf_url: HuggingFace dataset URL
        
    Returns:
        Validation result with metadata
    """
    try:
        hf_service = HuggingFaceService()
        
        # Validate URL format
        org_dataset = hf_service.validate_hf_url(hf_url)
        if not org_dataset:
            return {"valid": False, "error": "Invalid HuggingFace URL format"}
        
        # Extract dataset info
        info = hf_service.extract_dataset_info(hf_url)
        if not info:
            return {"valid": False, "error": "Could not access dataset"}
        
        return {
            "valid": True,
            "dataset_info": info,
            "org": org_dataset[0],
            "dataset_name": org_dataset[1]
        }
        
    except Exception as e:
        logger.error(f"HF URL validation failed: {e}")
        return {"valid": False, "error": str(e)}