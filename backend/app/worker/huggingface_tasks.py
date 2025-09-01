"""
Celery tasks for HuggingFace dataset processing
"""

import logging
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from celery import current_task
from app.worker.celery_app import celery_app
from app.services.huggingface import HuggingFaceService
from app.services.datasets import DatasetService
from app.schemas.dataset import SceneCreate
from app.core.config import settings

logger = logging.getLogger(__name__)

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
    try:
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'status': 'initializing', 'processed': 0, 'total': 0}
        )
        
        logger.info(f"Starting HF dataset processing: {hf_dataset_url} for dataset {dataset_id}")
        
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
                    height=image_data['height'],
                    attrs={
                        'hf_index': image_data['hf_index'],
                        'hf_split': split,
                        'hf_metadata': image_data.get('metadata', {})
                    }
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
            "failed_scenes": failed_scenes
        }
        
        logger.info(f"HF dataset processing completed: {result}")
        
        self.update_state(
            state='SUCCESS',
            meta=result
        )
        
        return result
        
    except Exception as e:
        logger.error(f"HF dataset processing failed: {e}")
        
        # Retry on certain errors
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying HF processing (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)
        
        error_result = {
            "status": "failed",
            "error": str(e),
            "processed_scenes": 0,
            "failed_scenes": 0
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