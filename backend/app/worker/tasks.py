"""
Celery tasks for background job processing
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from celery import current_task
from app.worker.celery_app import celery_app
from app.services.jobs import JobService
from app.services.datasets import DatasetService
from app.services.scenes import SceneService
from app.services.ai_pipeline import process_scene_ai
from app.services.storage import StorageService
from app.core.supabase import init_supabase, get_supabase
from app.core.redis import init_redis

logger = logging.getLogger(__name__)

def run_async(coro):
    """Helper to run async functions in Celery tasks"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

async def _create_scene_objects(scene_id: str, objects_data: list):
    """Create object records in database from RunPod object detection results"""
    from app.core.supabase import get_supabase
    import uuid
    
    if not objects_data:
        return
    
    supabase = get_supabase()
    
    # Convert RunPod objects to database format
    db_objects = []
    for i, obj in enumerate(objects_data):
        # Handle different RunPod object formats
        # Format 1: {category, confidence, bbox: {x, y, width, height}, ...}
        # Format 2: {label, confidence, bbox: [x1, y1, x2, y2], ...}
        bbox_data = obj.get("bbox", {})
        
        # Handle bbox as list [x1, y1, x2, y2] (RunPod format)
        if isinstance(bbox_data, list) and len(bbox_data) == 4:
            x1, y1, x2, y2 = bbox_data
            bbox = {
                'x': x1,
                'y': y1, 
                'width': x2 - x1,
                'height': y2 - y1
            }
        # Handle bbox as dict {x, y, width, height}
        elif isinstance(bbox_data, dict):
            bbox = bbox_data
        else:
            # Default fallback
            bbox = {'x': 0, 'y': 0, 'width': 0, 'height': 0}
        
        # Normalize category to match database schema
        category = obj.get("category", obj.get("label", "furniture"))  # Default fallback
        # Convert RunPod categories to our canonical categories
        category_mapping = {
            "sofa": "sofa",
            "chair": "chair", 
            "table": "table",
            "bed": "bed",
            "cabinet": "cabinet",
            "shelf": "shelf",
            "lamp": "lamp",
            "plant": "plant",
            "artwork": "artwork",
            "mirror": "mirror",
            "cushion": "cushion",
            "rug": "rug",
            "curtain": "curtain"
        }
        normalized_category = category_mapping.get(category.lower(), "furniture")  # Default to "furniture"

        db_object = {
            "id": str(uuid.uuid4()),
            "scene_id": scene_id,
            "category_code": normalized_category,
            "confidence": float(obj.get("confidence", 0.0)),
            "bbox_x": bbox.get("x", 0),
            "bbox_y": bbox.get("y", 0), 
            "bbox_w": bbox.get("width", 0),  # Fixed: bbox_w instead of bbox_width
            "bbox_h": bbox.get("height", 0),  # Fixed: bbox_h instead of bbox_height  
            "mask_key": obj.get("mask_key", obj.get("r2_mask_key")),  # Try both field names
            "thumb_key": obj.get("thumb_key", obj.get("r2_thumb_key")),  # R2 thumbnail key
            "depth_key": obj.get("depth_key", obj.get("r2_depth_key")),  # R2 depth key
            "subcategory": obj.get("subcategory"),
            "description": obj.get("description", obj.get("caption")),  # Try description or caption
            "attrs": obj.get("attrs", obj.get("attributes"))  # Additional object attributes
        }
        
        # Add RunPod-specific attributes to attrs if not already present
        if not db_object.get("attrs"):
            attrs = {}
            if obj.get("area"):
                attrs["area"] = obj.get("area")
            if obj.get("has_mask") is not None:
                attrs["has_mask"] = obj.get("has_mask")
            if obj.get("mask_area"):
                attrs["mask_area"] = obj.get("mask_area")
            if obj.get("mask_coverage"):
                attrs["mask_coverage"] = obj.get("mask_coverage")
            if obj.get("segmentation_confidence"):
                attrs["segmentation_confidence"] = obj.get("segmentation_confidence")
            if obj.get("color"):
                attrs["color"] = obj.get("color")
            if obj.get("material"):
                attrs["material"] = obj.get("material")
            if obj.get("style"):
                attrs["style"] = obj.get("style")
            
            if attrs:  # Only set attrs if we have any attributes
                db_object["attrs"] = attrs
        
        # Filter out None values
        db_object = {k: v for k, v in db_object.items() if v is not None}
        db_objects.append(db_object)
    
    try:
        # Insert objects in batch
        result = supabase.table("objects").insert(db_objects).execute()
        created_objects = result.data
        logger.info(f"Created {len(created_objects)} object records for scene {scene_id}")
        
        # Extract materials from RunPod response and create object_materials records
        materials_to_insert = []
        
        for i, obj in enumerate(objects_data):
            if i < len(created_objects):
                object_id = created_objects[i]["id"]
                
                # Extract materials from object data
                materials = obj.get("materials", [])
                if isinstance(materials, list):
                    for material_info in materials:
                        if isinstance(material_info, dict):
                            material_code = material_info.get("material", material_info.get("name"))
                            confidence = material_info.get("confidence", 0.5)
                        elif isinstance(material_info, str):
                            material_code = material_info
                            confidence = 0.5  # Default confidence
                        else:
                            continue
                            
                        if material_code:
                            materials_to_insert.append({
                                "object_id": object_id,
                                "material_code": material_code.lower(),
                                "conf": float(confidence)
                            })
                
                # Also check if material is stored as a single field
                single_material = obj.get("material")
                if single_material and isinstance(single_material, str):
                    materials_to_insert.append({
                        "object_id": object_id,
                        "material_code": single_material.lower(),
                        "conf": float(obj.get("material_confidence", 0.5))
                    })
        
        # Insert materials if any were found
        if materials_to_insert:
            try:
                materials_result = supabase.table("object_materials").insert(materials_to_insert).execute()
                logger.info(f"Created {len(materials_result.data)} material records for scene {scene_id}")
            except Exception as e:
                logger.warning(f"Failed to insert materials for scene {scene_id}: {e}")
        
    except Exception as e:
        logger.error(f"Failed to create objects for scene {scene_id}: {e}")
        raise

@celery_app.task(bind=True, name='process_dataset', max_retries=3, default_retry_delay=60)
def process_dataset(self, job_id: str, dataset_id: str, options: Dict[str, Any] = None):
    """
    Process an entire dataset - main background job for dataset ingestion
    """
    logger.info(f"Starting dataset processing job {job_id} for dataset {dataset_id}")
    
    async def _process():
        # Initialize connections for worker process
        await init_supabase()
        await init_redis()
        
        job_service = JobService()
        dataset_service = DatasetService()
        
        try:
            # Update job status to running
            await job_service.update_job(job_id, {
                "status": "running",
                "started_at": datetime.utcnow().isoformat()
            })
            
            # Add job event
            await job_service.add_job_event(job_id, "started", {
                "stage": "dataset_processing",
                "dataset_id": dataset_id
            })
            
            # Get dataset info
            dataset = await dataset_service.get_dataset(dataset_id)
            if not dataset:
                raise Exception(f"Dataset {dataset_id} not found")
            
            # Simulate dataset processing steps
            stages = [
                ("validating", "Validating dataset structure"),
                ("scanning", "Scanning for images"),
                ("preprocessing", "Preprocessing images"),
                ("extracting", "Extracting metadata"),
                ("registering", "Registering scenes")
            ]
            
            total_stages = len(stages)
            for i, (stage, description) in enumerate(stages):
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': total_stages,
                        'stage': stage,
                        'description': description
                    }
                )
                
                # Add stage event
                await job_service.add_job_event(job_id, "progress", {
                    "stage": stage,
                    "description": description,
                    "progress": (i + 1) / total_stages * 100
                })
                
                # Simulate processing time
                await asyncio.sleep(2)
            
            # Complete the job
            await job_service.update_job(job_id, {
                "status": "succeeded",
                "finished_at": datetime.utcnow().isoformat(),
                "result": {
                    "processed_scenes": 10,  # Mock result
                    "success_rate": 100,
                    "processing_time": 10
                }
            })
            
            await job_service.add_job_event(job_id, "completed", {
                "stage": "finished",
                "processed_scenes": 10
            })
            
            logger.info(f"Dataset processing job {job_id} completed successfully")
            return {"status": "success", "processed_scenes": 10}
            
        except Exception as e:
            logger.error(f"Dataset processing job {job_id} failed: {e}")
            
            # Check if we should retry
            if self.request.retries < self.max_retries:
                logger.info(f"Retrying dataset processing (attempt {self.request.retries + 1}/{self.max_retries})")
                
                # Add retry event
                await job_service.add_job_event(job_id, "retry", {
                    "attempt": self.request.retries + 1,
                    "max_retries": self.max_retries,
                    "error": str(e),
                    "stage": "retry"
                })
                
                # Mark job as running (retrying)
                await job_service.update_job(job_id, {
                    "status": "running",
                    "error": f"Attempt {self.request.retries + 1}/{self.max_retries}: {str(e)}"
                })
                
                raise self.retry(exc=e)
            
            # Mark job as failed after all retries exhausted
            await job_service.update_job(job_id, {
                "status": "failed",
                "finished_at": datetime.utcnow().isoformat(),
                "error": str(e)
            })
            
            await job_service.add_job_event(job_id, "failed", {
                "error": str(e),
                "stage": "error",
                "retries_exhausted": True
            })
            
            raise e
    
    return run_async(_process())

@celery_app.task(bind=True, name='process_scene', max_retries=2, default_retry_delay=30)
def process_scene(self, job_id: str, scene_id: str, options: Dict[str, Any] = None):
    """
    Process a single scene - AI analysis pipeline
    """
    logger.info(f"Starting scene processing job {job_id} for scene {scene_id}")
    
    async def _process():
        # Initialize connections for worker process
        await init_supabase()
        await init_redis()
        
        job_service = JobService()
        scene_service = SceneService()
        
        try:
            # Update job status
            await job_service.update_job(job_id, {
                "status": "running",
                "started_at": datetime.utcnow().isoformat()
            })
            
            await job_service.add_job_event(job_id, "started", {
                "stage": "scene_processing",
                "scene_id": scene_id
            })
            
            # Get scene info
            scene = await scene_service.get_scene(scene_id, include_objects=False)
            if not scene:
                raise Exception(f"Scene {scene_id} not found")
            
            # Real AI processing pipeline
            storage_service = StorageService()
            
            # Load image from R2 storage
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'current': 1,
                    'total': 8,
                    'stage': 'loading',
                    'description': 'Loading image from storage',
                    'scene_id': scene_id
                }
            )
            
            await job_service.add_job_event(job_id, "progress", {
                "stage": "loading",
                "description": "Loading image from storage",
                "scene_id": scene_id,
                "progress": 12.5
            })
            
            # Get scene info to find R2 image key
            scene_data = await scene_service.get_scene(scene_id, include_objects=False)
            r2_key = scene_data.get('r2_key_original') if scene_data else None
            if not scene_data or not r2_key:
                raise Exception(f"Scene {scene_id} missing image data")
            
            # Download image from R2
            image_data = await storage_service.download_object(r2_key)
            if not image_data:
                raise Exception(f"Failed to download image for scene {scene_id}")
            
            # Run AI pipeline stages with progress updates
            ai_stages = [
                ("scene_classification", "Classifying scene type"),
                ("object_detection", "Detecting objects"), 
                ("style_analysis", "Analyzing design style"),
                ("depth_estimation", "Estimating depth"),
                ("color_analysis", "Analyzing color palette"),
                ("material_classification", "Classifying materials"),
                ("quality_assessment", "Final quality assessment")
            ]
            
            # Update progress for AI processing start
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'current': 2,
                    'total': 8,
                    'stage': 'ai_processing',
                    'description': 'Running AI analysis',
                    'scene_id': scene_id
                }
            )
            
            await job_service.add_job_event(job_id, "progress", {
                "stage": "ai_processing", 
                "description": "Starting AI analysis pipeline",
                "scene_id": scene_id,
                "progress": 25.0
            })
            
            # Process scene with real AI pipeline
            ai_results = await process_scene_ai(
                image_data=image_data,
                scene_id=scene_id,
                options=options or {}
            )
            
            # Update progress through remaining stages
            for i, (stage, description) in enumerate(ai_stages, start=3):
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i,
                        'total': 8,
                        'stage': stage,
                        'description': description,
                        'scene_id': scene_id
                    }
                )
                
                await job_service.add_job_event(job_id, "progress", {
                    "stage": stage,
                    "description": description,
                    "scene_id": scene_id, 
                    "progress": (i / 8) * 100
                })
                
                # Small delay for realistic progress
                await asyncio.sleep(0.5)
            
            # Prepare final results
            processing_results = {
                "status": "processed",
                "scene_type": ai_results.get("scene_type", "unknown"),
                "scene_conf": ai_results.get("scene_conf", 0.0),
                "primary_style": ai_results.get("primary_style", "contemporary"),
                "style_confidence": ai_results.get("style_confidence", 0.0),
                "objects_detected": ai_results.get("objects_detected", 0),
                "objects": ai_results.get("objects", []),  # Include actual objects array
                "color_analysis": ai_results.get("dominant_color", {}),
                "depth_available": ai_results.get("depth_available", False),
                "processing_success": ai_results.get("success", False),
                "ai_error": ai_results.get("error") if not ai_results.get("success") else None
            }
            
            await scene_service.update_scene(scene_id, processing_results)
            
            # Create object records from RunPod results
            objects_data = ai_results.get("objects", [])
            if objects_data:
                logger.info(f"Creating {len(objects_data)} object records for scene {scene_id}")
                await _create_scene_objects(scene_id, objects_data)
            
            # Get current job to preserve existing metadata
            current_job = await job_service.get_job(job_id)
            existing_meta = current_job.meta if current_job and current_job.meta else {}
            
            # Complete job
            await job_service.update_job(job_id, {
                "status": "succeeded", 
                "finished_at": datetime.utcnow().isoformat(),
                "meta": {
                    **existing_meta,  # Preserve original metadata
                    "result": processing_results,
                    "processing_type": "scene_ai"
                }
            })
            
            await job_service.add_job_event(job_id, "completed", {
                "stage": "finished",
                "scene_id": scene_id,
                **processing_results
            })
            
            logger.info(f"Scene processing job {job_id} completed successfully")
            return processing_results
            
        except Exception as e:
            logger.error(f"Scene processing job {job_id} failed: {e}")
            
            # Check if we should retry
            if self.request.retries < self.max_retries:
                logger.info(f"Retrying scene processing (attempt {self.request.retries + 1}/{self.max_retries})")
                
                # Add retry event
                await job_service.add_job_event(job_id, "retry", {
                    "attempt": self.request.retries + 1,
                    "max_retries": self.max_retries,
                    "error": str(e),
                    "scene_id": scene_id,
                    "stage": "retry"
                })
                
                # Mark job as running (retrying)
                await job_service.update_job(job_id, {
                    "status": "running",
                    "error": f"Attempt {self.request.retries + 1}/{self.max_retries}: {str(e)}"
                })
                
                raise self.retry(exc=e)
            
            # Mark job as failed after all retries exhausted
            await job_service.update_job(job_id, {
                "status": "failed",
                "finished_at": datetime.utcnow().isoformat(),
                "error": str(e)
            })
            
            await job_service.add_job_event(job_id, "failed", {
                "error": str(e),
                "scene_id": scene_id,
                "stage": "error",
                "retries_exhausted": True
            })
            
            raise e
    
    return run_async(_process())

@celery_app.task(bind=True, name='cleanup_job')
def cleanup_job(self, job_id: str):
    """
    Cleanup job - remove temporary files and old job data
    """
    logger.info(f"Starting cleanup job {job_id}")
    
    async def _cleanup():
        job_service = JobService()
        
        try:
            # Mock cleanup operations
            await asyncio.sleep(1)
            
            await job_service.add_job_event(job_id, "cleanup_completed", {
                "stage": "maintenance",
                "cleaned_files": 0  # Mock
            })
            
            logger.info(f"Cleanup job {job_id} completed")
            return {"status": "success", "cleaned_files": 0}
            
        except Exception as e:
            logger.error(f"Cleanup job {job_id} failed: {e}")
            raise e
    
    return run_async(_cleanup())

# Task result callbacks
@celery_app.task(bind=True)
def task_success_handler(self, retval, task_id, args, kwargs):
    """Handle successful task completion"""
    logger.info(f"Task {task_id} completed successfully: {retval}")

@celery_app.task(bind=True)
def task_failure_handler(self, task_id, error, traceback, args, kwargs):
    """Handle task failure"""
    logger.error(f"Task {task_id} failed with error: {error}")
    logger.error(f"Traceback: {traceback}")

@celery_app.task(bind=True, name='process_scenes_in_dataset', max_retries=1)
def process_scenes_in_dataset(self, job_id: str, dataset_id: str, options: Dict[str, Any] = None):
    """
    Process all scenes in a dataset with AI pipeline
    Triggered automatically after successful data ingestion
    """
    current_task = self
    logger.info(f"Starting AI processing for dataset {dataset_id} - Job {job_id}")
    
    async def _process():
        # Initialize connections for worker process
        await init_supabase()
        await init_redis()
        
        job_service = JobService()
        scene_service = SceneService()
        
        try:
            # Update job status
            await job_service.update_job(job_id, {
                "status": "running",
                "started_at": datetime.utcnow().isoformat()
            })
            
            await job_service.add_job_event(job_id, "started", {
                "stage": "ai_processing",
                "dataset_id": dataset_id,
                "trigger": options.get("trigger", "manual") if options else "manual"
            })
            
            # Get scenes to process
            if options and "scene_ids" in options:
                # Process specific scenes
                scene_ids = options["scene_ids"]
                logger.info(f"Processing {len(scene_ids)} specific scenes")
            else:
                # Get all scenes in dataset
                scenes_result = await scene_service.get_scenes_by_dataset(dataset_id)
                scene_ids = [str(scene.id) for scene in scenes_result["data"]]
                logger.info(f"Processing all {len(scene_ids)} scenes in dataset")
            
            if not scene_ids:
                raise Exception(f"No scenes found to process in dataset {dataset_id}")
            
            total_scenes = len(scene_ids)
            processed_count = 0
            failed_count = 0
            
            # Process each scene individually
            for idx, scene_id in enumerate(scene_ids):
                try:
                    # Update progress
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'current': idx + 1,
                            'total': total_scenes,
                            'stage': 'ai_processing',
                            'description': f'Processing scene {idx + 1}/{total_scenes}',
                            'scene_id': scene_id,
                            'processed': processed_count,
                            'failed': failed_count
                        }
                    )
                    
                    await job_service.add_job_event(job_id, "progress", {
                        "stage": "ai_processing",
                        "description": f"Processing scene {idx + 1}/{total_scenes}",
                        "scene_id": scene_id,
                        "progress": (idx + 1) / total_scenes * 100,
                        "processed": processed_count,
                        "failed": failed_count
                    })
                    
                    # Trigger individual scene processing task
                    scene_job_id = f"{job_id}_scene_{idx}"
                    scene_task = process_scene.delay(scene_job_id, scene_id, {
                        "parent_job": job_id,
                        "dataset_id": dataset_id,
                        "scene_index": idx + 1,
                        "total_scenes": total_scenes
                    })
                    
                    # Wait for scene processing to complete (with timeout)
                    scene_result = scene_task.get(timeout=300)  # 5 minute timeout per scene
                    processed_count += 1
                    
                    logger.info(f"Successfully processed scene {idx + 1}/{total_scenes}: {scene_id}")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to process scene {idx + 1}/{total_scenes} ({scene_id}): {e}")
                    
                    await job_service.add_job_event(job_id, "scene_failed", {
                        "scene_id": scene_id,
                        "error": str(e),
                        "scene_index": idx + 1
                    })
                    
                    # Continue processing other scenes
                    continue
            
            # Update final job status
            final_status = "succeeded" if failed_count == 0 else ("partial_success" if processed_count > 0 else "failed")
            
            await job_service.update_job(job_id, {
                "status": "succeeded" if final_status == "succeeded" else "failed",
                "finished_at": datetime.utcnow().isoformat(),
                "meta": {
                    "total_scenes": total_scenes,
                    "processed_scenes": processed_count,
                    "failed_scenes": failed_count,
                    "success_rate": (processed_count / total_scenes * 100) if total_scenes > 0 else 0,
                    "trigger": options.get("trigger", "manual") if options else "manual",
                    "dataset_id": dataset_id
                }
            })
            
            await job_service.add_job_event(job_id, "completed", {
                "stage": "ai_processing",
                "total_scenes": total_scenes,
                "processed_scenes": processed_count,
                "failed_scenes": failed_count,
                "success_rate": (processed_count / total_scenes * 100) if total_scenes > 0 else 0
            })
            
            result = {
                "status": "completed",
                "total_scenes": total_scenes,
                "processed_scenes": processed_count,
                "failed_scenes": failed_count,
                "success_rate": (processed_count / total_scenes * 100) if total_scenes > 0 else 0
            }
            
            current_task.update_state(
                state='SUCCESS',
                meta=result
            )
            
            logger.info(
                f"AI processing completed for dataset {dataset_id}",
                extra={
                    "job_id": job_id,
                    "dataset_id": dataset_id,
                    "total_scenes": total_scenes,
                    "processed_scenes": processed_count,
                    "failed_scenes": failed_count,
                    "success_rate": (processed_count / total_scenes * 100) if total_scenes > 0 else 0
                }
            )
            
            return result
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"AI processing failed for dataset {dataset_id}: {error_message}")
            
            # Update job status to failed
            await job_service.update_job(job_id, {
                "status": "failed",
                "finished_at": datetime.utcnow().isoformat(),
                "meta": {
                    "error": error_message,
                    "dataset_id": dataset_id
                }
            })
            
            await job_service.add_job_event(job_id, "failed", {
                "error": error_message,
                "stage": "ai_processing"
            })
            
            current_task.update_state(
                state='FAILURE',
                meta={'error': error_message}
            )
            
            raise e
    
    return run_async(_process())