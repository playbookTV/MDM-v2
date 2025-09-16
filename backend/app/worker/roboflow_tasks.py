"""
Celery tasks for Roboflow dataset processing
"""

import logging
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime, timezone
import traceback
from uuid import uuid4

from celery import current_task
from app.worker.celery_app import celery_app
from app.services.roboflow import RoboflowService
from app.services.datasets import DatasetService
from app.services.jobs import JobService
from app.schemas.dataset import SceneCreate
from app.core.config import settings
from app.core.supabase import init_supabase
from app.core.redis import init_redis

logger = logging.getLogger(__name__)


def run_async_safe(coro):
    """Safe async runner for Celery tasks to avoid scope issues"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


async def _find_or_create_job_record(dataset_id: str, roboflow_url: str, celery_task_id: str) -> str:
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
                    "roboflow_url": roboflow_url,
                    "processing_type": "roboflow"
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
                "roboflow_url": roboflow_url,
                "processing_type": "roboflow"
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
def process_roboflow_dataset(
    self,
    dataset_id: str,
    roboflow_dataset_url: str,
    api_key: str,
    export_format: str = "coco",
    max_images: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process Roboflow dataset: download images and create scene records.
    
    Args:
        dataset_id: Supabase dataset ID
        roboflow_dataset_url: Roboflow Universe dataset URL
        api_key: Roboflow API key
        export_format: Export format (coco, yolov8, etc.)
        max_images: Maximum images to process
        
    Returns:
        Processing results dictionary
        
    Example:
        >>> result = process_roboflow_dataset.delay(
        ...     "dataset-123",
        ...     "https://universe.roboflow.com/roboflow-100/furniture-ngpea/model/1",
        ...     "your_api_key"
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
            dataset_id, roboflow_dataset_url, self.request.id
        )
        
        logger.info(
            f"Starting Roboflow dataset processing",
            extra={
                "celery_task_id": self.request.id,
                "job_id": job_id,
                "dataset_id": dataset_id,
                "roboflow_url": roboflow_dataset_url,
                "max_images": max_images
            }
        )
        
        return job_id, job_service
    
    try:
        # Run async initialization
        job_id, job_service = run_async_safe(_async_wrapper())
        
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'status': 'initializing', 'processed': 0, 'total': 0, 'job_id': job_id}
        )
        
        # Update job status to running
        if job_service:
            run_async_safe(job_service.update_job(job_id, {
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat()
            }))
        
        # Initialize services
        roboflow_service = RoboflowService()
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
        
        # Load images from Roboflow
        self.update_state(
            state='PROGRESS',
            meta={'status': 'loading_roboflow_dataset', 'processed': 0, 'total': 0}
        )
        
        images = roboflow_service.load_roboflow_dataset_images(
            roboflow_url=roboflow_dataset_url,
            api_key=api_key,
            export_format=export_format,
            max_images=max_images
        )
        
        if not images:
            logger.error(f"No images loaded from Roboflow dataset: {roboflow_dataset_url}")
            return {"status": "failed", "error": "No images found in dataset"}
        
        total_images = len(images)
        logger.info(f"Loaded {total_images} images from Roboflow dataset")
        
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
                            'current_image': f"roboflow_image_{image_data['roboflow_index']}"
                        }
                    )
                
                # Upload image to R2 - using sync version for Celery
                filename = image_data.get('filename', f"roboflow_image_{image_data['roboflow_index']}.jpg")
                r2_key = roboflow_service.upload_image_to_r2_sync(
                    image_data['image'], 
                    filename
                )
                
                if not r2_key:
                    logger.warning(f"Failed to upload image {idx} to R2")
                    failed_scenes += 1
                    continue
                
                # Process existing Roboflow metadata to avoid redundant AI processing
                metadata_result = roboflow_service.handle_existing_roboflow_metadata(
                    metadata=image_data['metadata'],
                    scene_id="temp",  # Will be replaced after scene creation
                    roboflow_index=image_data['roboflow_index']
                )
                
                # Create scene record with any pre-existing metadata - using sync version for Celery
                base_scene_data = {
                    "source": f"roboflow:{roboflow_dataset_url}",
                    "r2_key_original": r2_key,
                    "width": image_data['width'],
                    "height": image_data['height']
                }
                
                # Merge in metadata-derived scene updates and store skip_ai flags
                scene_data_dict = {**base_scene_data, **metadata_result["scene_updates"]}
                
                # Add skip_ai flags to scene attributes for later retrieval during AI processing
                if "attrs" not in scene_data_dict:
                    scene_data_dict["attrs"] = {}
                scene_data_dict["attrs"]["skip_ai"] = metadata_result["skip_ai"]
                
                scene_data = SceneCreate(**scene_data_dict)
                scene = dataset_service.create_scene_sync(dataset_id, scene_data)
                processed_scenes.append(scene.id)
                
                # Create object records from Roboflow metadata if any were found
                if metadata_result["objects_data"]:
                    logger.info(f"Creating {len(metadata_result['objects_data'])} objects from Roboflow metadata for scene {scene.id}")
                    # Import here to avoid circular imports
                    from app.worker.tasks import _create_scene_objects
                    import asyncio
                    
                    # Convert Roboflow objects to database format
                    roboflow_objects_for_db = []
                    for obj in metadata_result["objects_data"]:
                        roboflow_obj_db = {
                            "category": obj["category"],
                            "confidence": obj["confidence"],
                            "bbox": obj["bbox"],  # Already normalized to [x, y, w, h]
                            "description": obj.get("description"),
                            "attrs": obj.get("attributes", {})
                        }
                        roboflow_objects_for_db.append(roboflow_obj_db)
                    
                    # Use existing object creation logic
                    try:
                        run_async_safe(_create_scene_objects(scene.id, roboflow_objects_for_db))
                        logger.info(f"Successfully created Roboflow objects for scene {scene.id}")
                    except Exception as e:
                        logger.error(f"Failed to create Roboflow objects for scene {scene.id}: {e}")
                        # Continue processing - object creation failure shouldn't stop scene processing
                
                # Log metadata processing results
                skip_components = [k for k, v in metadata_result["skip_ai"].items() if v]
                if skip_components:
                    logger.info(f"Scene {scene.id}: Will skip AI processing for: {', '.join(skip_components)}")
                else:
                    logger.info(f"Scene {scene.id}: Full AI processing will be performed")
                
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
            run_async_safe(job_service.update_job(job_id, {
                "status": "succeeded",
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "meta": {
                    **result,
                    "celery_task_id": self.request.id,
                    "roboflow_url": roboflow_dataset_url
                }
            }))
        
        logger.info(
            f"Roboflow dataset processing completed",
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
            
            # Create job record for AI processing BEFORE starting the task
            ai_job_id = str(uuid4())
            
            if job_service:
                from app.core.supabase import get_supabase
                supabase = get_supabase()
                
                job_data = {
                    "id": ai_job_id,
                    "dataset_id": dataset_id,
                    "kind": "process",
                    "status": "queued",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "meta": {
                        "trigger": "auto_after_ingestion",
                        "source_job": job_id,
                        "total_scenes": len(processed_scenes)
                    }
                }
                
                supabase.table("jobs").insert(job_data).execute()
                logger.info(f"Created AI processing job record {ai_job_id}")
            
            # Now trigger the AI processing task
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
            
            # Update job with Celery task ID
            if job_service:
                supabase.table("jobs").update({
                    "meta": {
                        "celery_task_id": ai_processing_task.id,
                        "trigger": "auto_after_ingestion",
                        "source_job": job_id,
                        "total_scenes": len(processed_scenes)
                    }
                }).eq("id", ai_job_id).execute()
                
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
            f"Roboflow dataset processing failed: {error_message}",
            extra={
                "job_id": job_id,
                "dataset_id": dataset_id,
                "roboflow_url": roboflow_dataset_url,
                "celery_task_id": self.request.id,
                "retry_count": self.request.retries,
                "traceback": error_traceback
            }
        )
        
        # Update job status to failed
        if job_service:
            try:
                run_async_safe(job_service.update_job(job_id, {
                    "status": "failed",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "error": error_message,
                    "meta": {
                        "celery_task_id": self.request.id,
                        "roboflow_url": roboflow_dataset_url,
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
            logger.info(f"Retrying Roboflow processing (attempt {self.request.retries + 1})")
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
def validate_roboflow_url(roboflow_url: str, api_key: str) -> Dict[str, Any]:
    """
    Validate Roboflow dataset URL and extract metadata.
    
    Args:
        roboflow_url: Roboflow Universe dataset URL
        api_key: Roboflow API key
        
    Returns:
        Validation result with metadata
    """
    try:
        roboflow_service = RoboflowService()
        
        # Validate URL format
        url_parts = roboflow_service.validate_roboflow_url(roboflow_url)
        if not url_parts:
            return {"valid": False, "error": "Invalid Roboflow Universe URL format"}
        
        workspace, project, version = url_parts
        
        # Extract dataset info
        info = roboflow_service.extract_dataset_info(roboflow_url, api_key)
        if not info:
            return {"valid": False, "error": "Could not access dataset or invalid API key"}
        
        return {
            "valid": True,
            "dataset_info": info,
            "workspace": workspace,
            "project": project,
            "version": version
        }
        
    except Exception as e:
        logger.error(f"Roboflow URL validation failed: {e}")
        return {"valid": False, "error": str(e)}