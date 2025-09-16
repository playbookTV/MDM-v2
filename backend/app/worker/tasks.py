"""
Celery tasks for background job processing
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Union, Tuple, List
from celery import current_task
from app.worker.celery_app import celery_app
from app.services.jobs import JobService
from app.services.datasets import DatasetService
from app.services.scenes import SceneService
from app.services.ai_pipeline import process_scene_ai
from app.services.storage import StorageService
from app.utils.bbox import validate_and_normalize_bbox
from app.core.supabase import init_supabase, get_supabase
from app.core.redis import init_redis
from app.core.taxonomy import get_canonical_label, get_category_for_item

logger = logging.getLogger(__name__)

# Bbox validation is now handled by app.utils.bbox module

def run_async(coro):
    """Helper to run async functions in Celery tasks"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

async def _create_scene_objects(scene_id: str, objects_data: list, mask_keys: dict = None, scene_materials: dict = None, thumb_keys: dict = None):
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
        # Format 2: {label, confidence, bbox: [x, y, width, height], ...} (ACTUAL RunPod format)
        bbox_data = obj.get("bbox", {})
        
        # Validate and normalize bbox using robust utilities
        try:
            bbox = validate_and_normalize_bbox(bbox_data, object_index=i)
        except ValueError as e:
            logger.error(f"Skipping object {i} due to invalid bbox: {e}")
            continue
        
        # Get canonical label and category using centralized taxonomy
        raw_label = obj.get("label", obj.get("category", "furniture"))
        canonical_label = get_canonical_label(raw_label)
        normalized_category = get_category_for_item(canonical_label)
        
        # Debug logging to trace final mapping
        logger.info(f"Object {i}: '{raw_label}' → canonical:'{canonical_label}' → category:'{normalized_category}'")
        
        # Set subcategory for more granular classification
        subcategory = None
        if canonical_label in ['sectional', 'loveseat', 'chaise_lounge']:
            subcategory = canonical_label
        elif canonical_label in ['dining_table', 'coffee_table', 'console_table']:
            subcategory = canonical_label  
        elif category.lower() in ['floor_lamp', 'table_lamp', 'pendant_light']:
            subcategory = category.lower()
        elif category.lower() in ['bookshelf', 'tv_stand', 'dresser']:
            subcategory = category.lower()
        elif category.lower() in ['platform_bed', 'bunk_bed', 'canopy_bed', 'bed_frame']:
            subcategory = category.lower()
        elif category.lower() == 'bed':
            subcategory = 'bed_frame'  # Default subcategory for generic bed detection

        # Get mask and thumbnail keys from uploaded R2 files
        uploaded_mask_key = None
        uploaded_thumb_key = None
        if mask_keys:
            uploaded_mask_key = mask_keys.get(f"object_{i}_mask_key")
        if thumb_keys:
            uploaded_thumb_key = thumb_keys.get(f"object_{i}_thumb_key")
            
        # Validate bbox dimensions before database insertion
        bbox_width = bbox.get("width", 0)
        bbox_height = bbox.get("height", 0)
        
        if bbox_width <= 0 or bbox_height <= 0:
            logger.error(f"CRITICAL: Object {i} has invalid bbox dimensions: width={bbox_width}, height={bbox_height}. Raw bbox: {bbox_data}. Skipping object.")
            continue  # Skip this object entirely
            
        db_object = {
            "id": str(uuid.uuid4()),
            "scene_id": scene_id,
            "category_code": normalized_category,
            "confidence": float(obj.get("confidence", 0.0)),
            "bbox_x": bbox.get("x", 0),
            "bbox_y": bbox.get("y", 0), 
            "bbox_w": bbox_width,  # Validated positive width
            "bbox_h": bbox_height,  # Validated positive height  
            "mask_key": uploaded_mask_key or obj.get("mask_key", obj.get("r2_mask_key")),  # Use uploaded key first, then fallback
            "thumb_key": uploaded_thumb_key or obj.get("thumb_key", obj.get("r2_thumb_key")),  # Use uploaded key first, then fallback
            "depth_key": obj.get("depth_key", obj.get("r2_depth_key")),  # R2 depth key
            "subcategory": subcategory or obj.get("subcategory"),
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
        
        # Extract materials from scene-level material analysis and apply to objects
        materials_to_insert = []
        
        if scene_materials and created_objects:
            logger.info(f"Processing scene-level materials: {scene_materials}")
            
            # Get dominant materials from scene analysis
            dominant_materials = scene_materials.get("dominant_materials", [])
            
            if dominant_materials:
                logger.info(f"Found {len(dominant_materials)} dominant materials from scene analysis")
                
                # Apply the top materials to all objects (since RunPod does scene-level material analysis)
                for obj_record in created_objects:
                    object_id = obj_record["id"]
                    
                    # Apply top 3 materials to each object
                    for material_info in dominant_materials[:3]:
                        if isinstance(material_info, dict):
                            material_code = material_info.get("material", "unknown")
                            confidence = material_info.get("confidence", 0.5)
                            
                            if material_code and material_code != "unknown":
                                materials_to_insert.append({
                                    "object_id": object_id,
                                    "material_code": material_code.lower(),
                                    "conf": float(confidence)
                                })
            else:
                logger.info("No dominant materials found in scene analysis")
        else:
            logger.info("No scene materials provided or no objects created")
        
        logger.info(f"Total materials to insert: {len(materials_to_insert)}")
        
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
                "meta": {
                    "processed_scenes": 10,  # Mock result
                    "success_rate": 100,
                    "processing_time": 10,
                    "processing_type": "dataset"
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
            
            # Extract skip_ai flags from scene attributes if available
            skip_ai_flags = None
            if scene_data and scene_data.get('attrs'):
                skip_ai_flags = scene_data['attrs'].get('skip_ai')
                if skip_ai_flags:
                    skipped_components = [k for k, v in skip_ai_flags.items() if v]
                    if skipped_components:
                        logger.info(f"Scene {scene_id}: Using stored skip_ai flags for: {', '.join(skipped_components)}")
            
            # Process scene with real AI pipeline, passing skip_ai flags
            ai_results = await process_scene_ai(
                image_data=image_data,
                scene_id=scene_id,
                options=options or {},
                skip_ai=skip_ai_flags
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
            
            # Process and upload generated files to R2
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'current': 7,
                    'total': 8,
                    'stage': 'file_upload',
                    'description': 'Uploading generated files to storage',
                    'scene_id': scene_id
                }
            )
            
            await job_service.add_job_event(job_id, "progress", {
                "stage": "file_upload",
                "description": "Uploading masks, depth maps, and thumbnails",
                "scene_id": scene_id,
                "progress": 87.5
            })
            
            # Upload scene-level files (thumbnail, depth map) to R2
            scene_file_keys = {}
            if ai_results.get("thumbnail_base64"):
                logger.info(f"Uploading thumbnail for scene {scene_id}")
            if ai_results.get("depth_analysis", {}).get("depth_base64"):
                logger.info(f"Uploading depth map for scene {scene_id}")
            
            scene_file_keys = await storage_service.upload_scene_files(
                scene_id=scene_id,
                thumbnail_base64=ai_results.get("thumbnail_base64"),
                depth_base64=ai_results.get("depth_analysis", {}).get("depth_base64")
            )
            logger.info(f"Uploaded scene files for {scene_id}: {scene_file_keys}")
            
            # Upload object mask and thumbnail files to R2
            objects_data = ai_results.get("objects", [])
            mask_keys = {}
            thumb_keys = {}
            if objects_data:
                logger.info(f"Uploading masks for {len(objects_data)} objects in scene {scene_id}")
                mask_keys = await storage_service.upload_object_masks(scene_id, objects_data)
                logger.info(f"Uploaded {len(mask_keys)} object masks for {scene_id}")
                
                logger.info(f"Uploading thumbnails for {len(objects_data)} objects in scene {scene_id}")
                thumb_keys = await storage_service.upload_object_thumbnails(scene_id, objects_data)
                logger.info(f"Uploaded {len(thumb_keys)} object thumbnails for {scene_id}")
            
            # Prepare final results with R2 keys
            processing_results = {
                "status": "processed",
                "scene_type": ai_results.get("scene_type", "unknown"),
                "scene_conf": ai_results.get("scene_conf", 0.0),
                "primary_style": ai_results.get("primary_style", "contemporary"),
                "style_confidence": ai_results.get("style_confidence", 0.0),
                "objects_detected": ai_results.get("objects_detected", 0),
                "objects": ai_results.get("objects", []),  # Include actual objects array
                "palette": ai_results.get("color_palette", ai_results.get("dominant_color", {})),  # Match database schema
                "depth_available": ai_results.get("depth_available", False),
                "processing_success": ai_results.get("success", False),
                "ai_error": ai_results.get("error") if not ai_results.get("success") else None,
                # Add R2 keys to scene record
                **scene_file_keys  # This adds thumb_key and depth_key if they exist
            }
            
            updated = await scene_service.update_scene(scene_id, processing_results)
            logger.info(f"Scene {scene_id} metadata updated: {updated}")
            
            # Create object records from RunPod results with mask keys
            objects_data = ai_results.get("objects", [])
            if objects_data:
                logger.info(f"Creating {len(objects_data)} object records for scene {scene_id}")
                scene_materials = ai_results.get("material_analysis", {})
                await _create_scene_objects(scene_id, objects_data, mask_keys, scene_materials, thumb_keys)
            
            # Get current job to preserve existing metadata
            current_job = await job_service.get_job(job_id)
            existing_meta = current_job.meta if current_job and current_job.meta else {}
            
            # Complete job
            await job_service.update_job(job_id, {
                "status": "succeeded", 
                "finished_at": datetime.utcnow().isoformat(),
                "meta": {
                    **existing_meta,  # Preserve original metadata
                    **processing_results,  # Include processing results directly in meta
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
            
            # Process scenes in parallel batches
            batch_size = options.get("batch_size", 3) if options else 3
            batch_size = max(1, min(batch_size, 8))  # Enforce limits
            
            processed_scenes = []
            failed_scenes = []
            
            # Process in batches with parallel execution
            for batch_start in range(0, len(scene_ids), batch_size):
                batch_end = min(batch_start + batch_size, len(scene_ids))
                batch_scene_ids = scene_ids[batch_start:batch_end]
                
                try:
                    # Update progress for batch
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'current': batch_end,
                            'total': total_scenes,
                            'stage': 'ai_processing',
                            'description': f'Processing batch {batch_start//batch_size + 1} ({len(batch_scene_ids)} scenes)',
                            'batch_size': len(batch_scene_ids),
                            'processed': len(processed_scenes),
                            'failed': len(failed_scenes)
                        }
                    )
                    
                    await job_service.add_job_event(job_id, "progress", {
                        "stage": "ai_processing",
                        "description": f"Processing batch {batch_start//batch_size + 1}/{(total_scenes + batch_size - 1)//batch_size}",
                        "progress": (batch_end / total_scenes * 100),
                        "processed": len(processed_scenes),
                        "failed": len(failed_scenes)
                    })
                    
                    # Process batch in parallel using concurrent scene processing
                    from app.worker.batch_helpers import process_scenes_batch
                    batch_results = await process_scenes_batch(
                        job_id, batch_scene_ids, dataset_id, job_service, options
                    )
                    
                    # Aggregate results
                    for result in batch_results:
                        if result.get("success", False):
                            processed_scenes.append(result["scene_id"])
                        else:
                            failed_scenes.append({
                                "scene_id": result["scene_id"],
                                "error": result.get("error", "Unknown error")
                            })
                    
                    logger.info(f"Batch {batch_start//batch_size + 1} completed: {len([r for r in batch_results if r.get('success')])}/{len(batch_results)} successful")
                    
                except Exception as e:
                    logger.error(f"Batch processing failed for scenes {batch_scene_ids}: {e}")
                    
                    # Mark entire batch as failed
                    for scene_id in batch_scene_ids:
                        failed_scenes.append({
                            "scene_id": scene_id,
                            "error": f"Batch processing failed: {str(e)}"
                        })
                        
                        await job_service.add_job_event(job_id, "scene_failed", {
                            "scene_id": scene_id,
                            "error": str(e),
                            "batch_error": True
                        })
            
            processed_count = len(processed_scenes)
            failed_count = len(failed_scenes)
            
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
