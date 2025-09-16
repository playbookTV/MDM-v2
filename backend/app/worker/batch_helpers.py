"""
Helper functions for batch scene processing
"""

import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


async def process_scenes_batch(
    job_id: str,
    scene_ids: List[str], 
    dataset_id: str,
    job_service: 'JobService',
    options: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Process a batch of scenes concurrently with retry logic and exponential backoff.
    
    Args:
        job_id: Parent job ID for tracking
        scene_ids: List of scene IDs to process
        dataset_id: Dataset containing the scenes
        job_service: Service for job management
        options: Processing options
        
    Returns:
        List of results for each scene
    """
    from app.services.scenes import SceneService
    from app.services.storage import StorageService
    from app.services.runpod_client import runpod_client
    from app.worker.tasks import _create_scene_objects
    
    scene_service = SceneService()
    storage_service = StorageService()
    
    # Load scene data and images concurrently
    async def load_scene_data(scene_id: str) -> Dict[str, Any]:
        try:
            # Get scene metadata
            scene_data = await scene_service.get_scene(scene_id, include_objects=False)
            if not scene_data or not scene_data.get('r2_key_original'):
                return {
                    "scene_id": scene_id,
                    "success": False,
                    "error": "Scene not found or missing image data"
                }
            
            # Download image from R2
            image_data = await storage_service.download_object(scene_data['r2_key_original'])
            if not image_data:
                return {
                    "scene_id": scene_id,
                    "success": False,
                    "error": "Failed to download scene image"
                }
            
            return {
                "scene_id": scene_id,
                "image_data": image_data,
                "scene_data": scene_data,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Failed to load scene {scene_id}: {e}")
            return {
                "scene_id": scene_id,
                "success": False,
                "error": str(e)
            }
    
    # Load all scene data concurrently
    logger.info(f"Loading {len(scene_ids)} scenes for batch processing")
    load_tasks = [load_scene_data(scene_id) for scene_id in scene_ids]
    loaded_scenes = await asyncio.gather(*load_tasks, return_exceptions=True)
    
    # Filter successful loads and prepare for RunPod
    valid_scenes = []
    results = []
    
    for load_result in loaded_scenes:
        if isinstance(load_result, Exception):
            results.append({
                "scene_id": "unknown",
                "success": False,
                "error": str(load_result)
            })
        elif not load_result.get("success", False):
            results.append(load_result)
        else:
            valid_scenes.append(load_result)
    
    if not valid_scenes:
        logger.warning("No valid scenes to process in batch")
        return results
    
    # Try RunPod batch processing with retry logic
    max_retries = 3
    base_delay = 2.0  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"RunPod batch attempt {attempt + 1}/{max_retries} for {len(valid_scenes)} scenes")
            
            # Prepare scenes for RunPod batch processing
            scenes_data = [
                {
                    "scene_id": scene["scene_id"],
                    "image_data": scene["image_data"]
                }
                for scene in valid_scenes
            ]
            
            # Process batch with RunPod
            batch_result = await runpod_client.process_scenes_batch_runpod(
                scenes_data=scenes_data,
                batch_size=len(scenes_data),  # Process all in one batch
                options=options
            )
            
            if batch_result.get("success", False):
                # Process successful RunPod results
                batch_results = batch_result.get("batch_results", [])
                
                for i, runpod_result in enumerate(batch_results):
                    scene = valid_scenes[i]
                    scene_id = scene["scene_id"]
                    
                    if runpod_result.get("status") == "success":
                        try:
                            # Process the RunPod result
                            await process_runpod_scene_result(
                                scene_id, runpod_result, scene["scene_data"], 
                                scene_service, storage_service
                            )
                            
                            results.append({
                                "scene_id": scene_id,
                                "success": True,
                                "processing_time": runpod_result.get("processing_time", 0)
                            })
                            
                        except Exception as e:
                            logger.error(f"Failed to process RunPod result for scene {scene_id}: {e}")
                            results.append({
                                "scene_id": scene_id,
                                "success": False,
                                "error": f"Result processing failed: {str(e)}"
                            })
                    else:
                        results.append({
                            "scene_id": scene_id,
                            "success": False,
                            "error": runpod_result.get("error", "RunPod processing failed")
                        })
                
                logger.info(f"✅ Batch processing completed on attempt {attempt + 1}")
                break  # Success, exit retry loop
                
            else:
                # RunPod batch failed
                error_msg = batch_result.get("error", "Unknown RunPod error")
                logger.warning(f"RunPod batch failed on attempt {attempt + 1}: {error_msg}")
                
                if attempt == max_retries - 1:
                    # Final attempt failed, mark all as failed
                    for scene in valid_scenes:
                        results.append({
                            "scene_id": scene["scene_id"],
                            "success": False,
                            "error": f"RunPod batch failed after {max_retries} attempts: {error_msg}"
                        })
                else:
                    # Wait with exponential backoff
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"Retrying RunPod batch in {delay}s...")
                    await asyncio.sleep(delay)
                    
        except Exception as e:
            logger.error(f"RunPod batch attempt {attempt + 1} failed with exception: {e}")
            
            if attempt == max_retries - 1:
                # Final attempt failed, mark all as failed
                for scene in valid_scenes:
                    results.append({
                        "scene_id": scene["scene_id"],
                        "success": False,
                        "error": f"RunPod batch failed after {max_retries} attempts: {str(e)}"
                    })
            else:
                # Wait with exponential backoff
                delay = base_delay * (2 ** attempt)
                logger.info(f"Retrying RunPod batch in {delay}s...")
                await asyncio.sleep(delay)
    
    return results


async def process_runpod_scene_result(
    scene_id: str,
    runpod_result: Dict[str, Any], 
    scene_data: Dict[str, Any],
    scene_service: 'SceneService',
    storage_service: 'StorageService'
) -> None:
    """Process individual RunPod scene result and update database"""
    from app.worker.tasks import _create_scene_objects
    
    # Extract AI results from RunPod response
    ai_results = runpod_result
    
    # Upload scene-level files (thumbnail, depth map) to R2
    scene_file_keys = {}
    if ai_results.get("thumbnail_base64"):
        logger.debug(f"Uploading thumbnail for scene {scene_id}")
    if ai_results.get("depth_analysis", {}).get("depth_base64"):
        logger.debug(f"Uploading depth map for scene {scene_id}")
    
    scene_file_keys = await storage_service.upload_scene_files(
        scene_id=scene_id,
        thumbnail_base64=ai_results.get("thumbnail_base64"),
        depth_base64=ai_results.get("depth_analysis", {}).get("depth_base64")
    )
    
    # Upload object mask and thumbnail files to R2
    objects_data = ai_results.get("objects", [])
    mask_keys = {}
    thumb_keys = {}
    if objects_data:
        logger.debug(f"Uploading masks for {len(objects_data)} objects in scene {scene_id}")
        mask_keys = await storage_service.upload_object_masks(scene_id, objects_data)
        
        logger.debug(f"Uploading thumbnails for {len(objects_data)} objects in scene {scene_id}")
        thumb_keys = await storage_service.upload_object_thumbnails(scene_id, objects_data)
    
    # Prepare final results with R2 keys
    processing_results = {
        "status": "processed",
        "scene_type": ai_results.get("scene_type", "unknown"),
        "scene_conf": ai_results.get("scene_conf", 0.0),
        "primary_style": ai_results.get("primary_style", "contemporary"), 
        "style_confidence": ai_results.get("style_confidence", 0.0),
        "objects_detected": ai_results.get("objects_detected", 0),
        "objects": ai_results.get("objects", []),
        "palette": ai_results.get("color_palette", ai_results.get("dominant_color", {})),
        "depth_available": ai_results.get("depth_available", False),
        "processing_success": True,
        **scene_file_keys  # Add R2 keys
    }
    
    # Update scene in database
    await scene_service.update_scene(scene_id, processing_results)
    logger.debug(f"Scene {scene_id} metadata updated")
    
    # Create object records from RunPod results
    if objects_data:
        logger.debug(f"Creating {len(objects_data)} object records for scene {scene_id}")
        scene_materials = ai_results.get("material_analysis", {})
        await _create_scene_objects(scene_id, objects_data, mask_keys, scene_materials, thumb_keys)