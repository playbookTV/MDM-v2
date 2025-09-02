"""
HuggingFace dataset import service
"""

import logging
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from datasets import load_dataset
    from huggingface_hub import HfApi
    HF_AVAILABLE = True
except ImportError as e:
    logger.warning(f"HuggingFace dependencies not available: {e}")
    HF_AVAILABLE = False
    load_dataset = None
    HfApi = None
import requests
from PIL import Image
import io
import uuid

from app.core.config import settings
from app.services.storage import StorageService
from app.services.datasets import DatasetService
from app.schemas.dataset import SceneCreate

logger = logging.getLogger(__name__)

class HuggingFaceService:
    """Service for importing datasets from HuggingFace Hub"""
    
    HF_URL_PATTERN = re.compile(r'^https://huggingface\.co/datasets/([\w-]+)/([\w-]+)(?:/.*)?$')
    
    def __init__(self):
        self.storage = StorageService()
        self.dataset_service = DatasetService()
        if HF_AVAILABLE:
            self.hf_api = HfApi()
        else:
            self.hf_api = None
    
    def validate_hf_url(self, url: str) -> Optional[tuple[str, str]]:
        """
        Validate HuggingFace dataset URL and extract org/dataset name.
        
        Args:
            url: HuggingFace dataset URL
            
        Returns:
            Tuple of (org, dataset_name) if valid, None otherwise
            
        Example:
            >>> svc = HuggingFaceService()
            >>> svc.validate_hf_url("https://huggingface.co/datasets/nlphuji/flickr30k")
            ('nlphuji', 'flickr30k')
        """
        match = self.HF_URL_PATTERN.match(url)
        return (match.group(1), match.group(2)) if match else None
    
    def extract_dataset_info(self, hf_url: str) -> Dict[str, Any]:
        """
        Extract basic metadata from HuggingFace dataset.
        
        Args:
            hf_url: HuggingFace dataset URL
            
        Returns:
            Dictionary with dataset info or empty dict on error
        """
        if not HF_AVAILABLE:
            logger.warning("HuggingFace dependencies not available")
            return {}
            
        try:
            org_dataset = self.validate_hf_url(hf_url)
            if not org_dataset:
                return {}
                
            org, dataset_name = org_dataset
            dataset_id = f"{org}/{dataset_name}"
            
            # Get basic dataset info
            dataset_info = self.hf_api.dataset_info(dataset_id)
            
            return {
                "dataset_id": dataset_id,
                "description": dataset_info.description or "",
                "tags": dataset_info.tags or [],
                "license": getattr(dataset_info, 'license', None),
                "splits": list(dataset_info.splits.keys()) if dataset_info.splits else [],
            }
            
        except Exception as e:
            logger.warning(f"Failed to extract HF dataset info from {hf_url}: {e}")
            return {}
    
    def _detect_image_column(self, item: Dict[str, Any], preferred_column: str = "image") -> Optional[str]:
        """
        Auto-detect the image column name in a HuggingFace dataset item.
        
        Args:
            item: First dataset item to examine
            preferred_column: Preferred column name to try first
            
        Returns:
            Name of the image column, or None if not found
        """
        # First try the preferred column
        if preferred_column in item:
            obj = item[preferred_column]
            if self._is_image_object(obj):
                return preferred_column
        
        # Try common image column names
        common_names = ["image", "img", "picture", "photo", "thumbnail", "jpeg", "png"]
        for name in common_names:
            if name in item:
                obj = item[name]
                if self._is_image_object(obj):
                    return name
        
        # Try all columns and look for image-like objects
        for key, value in item.items():
            if self._is_image_object(value):
                return key
                
        return None
    
    def _is_image_object(self, obj: Any) -> bool:
        """Check if an object looks like a PIL Image or image data"""
        if obj is None:
            return False
            
        # PIL Image object
        if hasattr(obj, 'save') and hasattr(obj, 'size'):
            return True
            
        # Dictionary with bytes (some HF formats)
        if isinstance(obj, dict) and 'bytes' in obj:
            return True
            
        return False
    
    def load_hf_dataset_images(
        self, 
        hf_url: str, 
        split: str = "train", 
        image_column: str = "image",
        max_images: Optional[int] = None,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Load images from HuggingFace dataset with retry logic.
        
        Args:
            hf_url: HuggingFace dataset URL
            split: Dataset split to load
            image_column: Column name containing images
            max_images: Maximum images to load (None for all)
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of image records with metadata
            
        Example:
            >>> svc = HuggingFaceService()
            >>> images = svc.load_hf_dataset_images("https://huggingface.co/datasets/nlphuji/flickr30k")
            >>> len(images) > 0
            True
        """
        if not HF_AVAILABLE:
            logger.error("HuggingFace dependencies not available")
            return []
            
        import time
        
        for attempt in range(max_retries):
            try:
                org_dataset = self.validate_hf_url(hf_url)
                if not org_dataset:
                    logger.error(f"Invalid HuggingFace URL: {hf_url}")
                    return []
                    
                org, dataset_name = org_dataset
                dataset_id = f"{org}/{dataset_name}"
                
                logger.info(f"Loading HF dataset {dataset_id}, split={split} (attempt {attempt + 1})")
                
                # Load dataset
                dataset = load_dataset(dataset_id, split=split, streaming=True)
                
                images = []
                detected_image_column = None
                
                for idx, item in enumerate(dataset):
                    if max_images and idx >= max_images:
                        break
                    
                    # Auto-detect image column on first item
                    if detected_image_column is None:
                        detected_image_column = self._detect_image_column(item, image_column)
                        if not detected_image_column:
                            logger.error(f"No image column found in dataset {dataset_id}")
                            break
                        if detected_image_column != image_column:
                            logger.info(f"Auto-detected image column: '{detected_image_column}' (instead of '{image_column}')")
                        
                    # Extract image using detected column
                    image_obj = item.get(detected_image_column)
                    if image_obj is None:
                        continue
                    
                    # Handle different image formats from HF
                    if hasattr(image_obj, 'save'):  # PIL Image
                        pil_image = image_obj
                    elif isinstance(image_obj, dict) and 'bytes' in image_obj:
                        pil_image = Image.open(io.BytesIO(image_obj['bytes']))
                    else:
                        logger.warning(f"Unknown image format in item {idx}")
                        continue
                    
                    # Get image metadata
                    width, height = pil_image.size
                    
                    images.append({
                        "image": pil_image,
                        "width": width,
                        "height": height,
                        "hf_index": idx,
                        "metadata": {k: v for k, v in item.items() if k != detected_image_column}
                    })
                    
                    if idx % 10 == 0:
                        logger.info(f"Loaded {idx + 1} images from HF dataset")
                
                logger.info(f"Successfully loaded {len(images)} images from {dataset_id}")
                return images
                
            except Exception as e:
                logger.warning(f"HF dataset loading attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    # Exponential backoff: wait 2, 4, 8 seconds
                    wait_time = 2 ** (attempt + 1)
                    logger.info(f"Retrying HF dataset load in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to load HF dataset {hf_url} after {max_retries} attempts")
                    return []
        
        return []
    
    async def upload_image_to_r2(self, pil_image: Image.Image, filename: str) -> Optional[str]:
        """
        Upload PIL image to R2 storage.
        
        Args:
            pil_image: PIL Image object
            filename: Base filename (will generate UUID-based key)
            
        Returns:
            R2 key if successful, None otherwise
        """
        try:
            # Generate R2 key
            file_id = str(uuid.uuid4())
            # Preserve original extension if present, default to jpg
            if '.' in filename:
                ext = filename.split('.')[-1].lower()
            else:
                ext = 'jpg'
            r2_key = f"scenes/{file_id}.{ext}"
            
            # Convert PIL image to bytes
            img_buffer = io.BytesIO()
            # Convert RGBA to RGB if needed
            if pil_image.mode == 'RGBA':
                pil_image = pil_image.convert('RGB')
            pil_image.save(img_buffer, format='JPEG', quality=95)
            img_bytes = img_buffer.getvalue()
            
            # Upload to R2
            await self.storage.upload_object(
                key=r2_key,
                data=img_bytes,
                content_type='image/jpeg'
            )
            
            return r2_key
            
        except Exception as e:
            logger.error(f"Failed to upload image {filename} to R2: {e}")
            return None
    
    def upload_image_to_r2_sync(self, pil_image: Image.Image, filename: str, max_retries: int = 3) -> Optional[str]:
        """
        Sync version for Celery tasks - upload PIL image to R2 storage with retry logic.
        
        Args:
            pil_image: PIL Image object
            filename: Base filename (will generate UUID-based key)
            max_retries: Maximum number of retry attempts
            
        Returns:
            R2 key if successful, None otherwise
        """
        import time
        from botocore.exceptions import ClientError
        
        for attempt in range(max_retries):
            try:
                # Generate R2 key
                file_id = str(uuid.uuid4())
                # Preserve original extension if present, default to jpg
                if '.' in filename:
                    ext = filename.split('.')[-1].lower()
                else:
                    ext = 'jpg'
                r2_key = f"scenes/{file_id}.{ext}"
                
                # Convert PIL image to bytes
                img_buffer = io.BytesIO()
                # Convert RGBA to RGB if needed
                if pil_image.mode == 'RGBA':
                    pil_image = pil_image.convert('RGB')
                pil_image.save(img_buffer, format='JPEG', quality=95)
                img_bytes = img_buffer.getvalue()
                
                # Upload directly to R2 using boto3 client (truly synchronous)
                self.storage.client.put_object(
                    Bucket=self.storage.bucket_name,
                    Key=r2_key,
                    Body=img_bytes,
                    ContentType='image/jpeg'
                )
                
                logger.debug(f"Successfully uploaded {filename} to R2 as {r2_key}")
                return r2_key
                
            except ClientError as e:
                logger.warning(f"Upload attempt {attempt + 1} failed for {filename} (AWS error): {e}")
                if attempt < max_retries - 1:
                    # Exponential backoff: wait 1, 2, 4 seconds
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying upload in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to upload image {filename} to R2 after {max_retries} attempts")
                    return None
            except Exception as e:
                logger.warning(f"Upload attempt {attempt + 1} failed for {filename}: {e}")
                if attempt < max_retries - 1:
                    # Exponential backoff: wait 1, 2, 4 seconds
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying upload in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to upload image {filename} to R2 after {max_retries} attempts")
                    return None
        
        return None