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
    
    def handle_existing_hf_metadata(self, metadata: Dict[str, Any], scene_id: str, hf_index: int) -> Dict[str, Any]:
        """
        Handle existing metadata from HuggingFace datasets to avoid redundant AI processing.
        
        Args:
            metadata: Raw HF dataset item metadata (excluding image column)
            scene_id: Database scene ID 
            hf_index: Original HF dataset index
            
        Returns:
            Dict with keys:
            - scene_updates: Dict of updates to apply to scene record
            - objects_data: List of object records to create (if any)
            - skip_ai: Dict indicating which AI components to skip
            
        Example:
            >>> svc = HuggingFaceService()
            >>> result = svc.handle_existing_hf_metadata({
            ...     "room_type": "living_room",
            ...     "caption": "A modern living room with sofa",
            ...     "objects": [{"category": "sofa", "bbox": [100, 200, 300, 400]}]
            ... }, "scene-123", 42)
            >>> result["scene_updates"]["scene_type"]
            'living_room'
            >>> result["skip_ai"]["scene_classification"]
            True
        """
        if not metadata or not isinstance(metadata, dict):
            return {
                "scene_updates": {},
                "objects_data": [],
                "skip_ai": {
                    "scene_classification": False,
                    "object_detection": False, 
                    "style_analysis": False,
                    "depth_estimation": False,
                    "color_analysis": False,
                    "material_classification": False
                }
            }
        
        scene_updates = {}
        objects_data = []
        skip_ai = {
            "scene_classification": False,
            "object_detection": False,
            "style_analysis": False, 
            "depth_estimation": False,
            "color_analysis": False,
            "material_classification": False
        }
        
        # Preserve all original metadata in attrs
        scene_updates["attrs"] = {
            **metadata,
            "hf_original_index": hf_index,
            "metadata_processed_at": datetime.utcnow().isoformat()
        }
        
        try:
            # Scene type mapping - Enhanced for more datasets
            scene_type_mapping = {
                "room_type": "scene_type",
                "scene_type": "scene_type", 
                "room": "scene_type",
                "room_category": "scene_type",
                "room_name": "scene_type",
                "space_type": "scene_type",
                "location": "scene_type",
                "place": "scene_type",
                "scene_category": "scene_type",
                "area_type": "scene_type",
                "indoor_scene": "scene_type"
            }
            
            for hf_key, db_key in scene_type_mapping.items():
                if hf_key in metadata:
                    scene_value = str(metadata[hf_key]).lower().strip()
                    # Map common room types - Enhanced for more datasets
                    room_type_mapping = {
                        "living_room": "living_room",
                        "livingroom": "living_room", 
                        "living": "living_room",
                        "lounge": "living_room",
                        "family_room": "living_room",
                        "sitting_room": "living_room",
                        "bedroom": "bedroom",
                        "bed_room": "bedroom",
                        "master_bedroom": "bedroom",
                        "guest_bedroom": "bedroom",
                        "kids_bedroom": "bedroom",
                        "kitchen": "kitchen",
                        "kitchenette": "kitchen",
                        "galley": "kitchen",
                        "bathroom": "bathroom", 
                        "bath_room": "bathroom",
                        "master_bathroom": "bathroom",
                        "powder_room": "bathroom",
                        "washroom": "bathroom",
                        "restroom": "bathroom",
                        "toilet": "bathroom",
                        "dining_room": "dining_room",
                        "diningroom": "dining_room",
                        "dining": "dining_room",
                        "breakfast_nook": "dining_room",
                        "dinette": "dining_room",
                        "office": "office",
                        "study": "office",
                        "home_office": "office",
                        "workspace": "office",
                        "den": "office",
                        "library": "office",
                        "garage": "garage",
                        "hallway": "hallway",
                        "corridor": "hallway",
                        "foyer": "hallway",
                        "entryway": "hallway",
                        "balcony": "balcony",
                        "patio": "balcony",
                        "terrace": "balcony",
                        "outdoor": "outdoor",
                        "garden": "outdoor",
                        "yard": "outdoor",
                        "basement": "basement",
                        "attic": "attic",
                        "laundry_room": "utility",
                        "utility_room": "utility",
                        "mudroom": "utility",
                        "pantry": "utility",
                        "closet": "storage",
                        "walk_in_closet": "storage"
                    }
                    
                    mapped_type = room_type_mapping.get(scene_value, scene_value)
                    confidence = metadata.get(f"{hf_key}_confidence", 0.8)  # Default confidence
                    
                    # Apply configuration thresholds and preferences
                    if (settings.PREFER_EXISTING_ANNOTATIONS and 
                        not settings.FORCE_AI_REPROCESSING and 
                        confidence >= settings.MIN_SCENE_CONFIDENCE):
                        
                        scene_updates["scene_type"] = mapped_type
                        scene_updates["scene_conf"] = confidence
                        skip_ai["scene_classification"] = True
                        logger.info(f"Scene {scene_id}: Mapped HF {hf_key}='{scene_value}' to scene_type='{mapped_type}' (conf={confidence:.2f})")
                    else:
                        logger.info(f"Scene {scene_id}: HF scene type '{scene_value}' below confidence threshold ({confidence:.2f} < {settings.MIN_SCENE_CONFIDENCE}), will reprocess")
                    break
                    
            # Description/caption mapping
            description_keys = ["caption", "description", "text", "summary", "title"]
            for desc_key in description_keys:
                if desc_key in metadata and metadata[desc_key]:
                    scene_updates["description"] = str(metadata[desc_key]).strip()
                    logger.info(f"Scene {scene_id}: Using HF {desc_key} as description")
                    break
                    
            # Style analysis mapping
            style_mapping = {
                "style": "primary_style",
                "design_style": "primary_style",
                "interior_style": "primary_style", 
                "decor_style": "primary_style"
            }
            
            for hf_key, db_key in style_mapping.items():
                if hf_key in metadata:
                    style_value = str(metadata[hf_key]).lower().strip()
                    confidence = metadata.get(f"{hf_key}_confidence", 0.7)
                    
                    # Apply configuration thresholds and preferences
                    if (settings.PREFER_EXISTING_ANNOTATIONS and 
                        not settings.FORCE_AI_REPROCESSING and 
                        confidence >= settings.MIN_STYLE_CONFIDENCE):
                        
                        scene_updates[db_key] = style_value
                        scene_updates["style_confidence"] = confidence
                        skip_ai["style_analysis"] = True
                        logger.info(f"Scene {scene_id}: Using HF style '{style_value}' (conf={confidence:.2f})")
                    else:
                        logger.info(f"Scene {scene_id}: HF style '{style_value}' below confidence threshold ({confidence:.2f} < {settings.MIN_STYLE_CONFIDENCE}), will reprocess")
                    break
                    
            # Color analysis mapping
            color_keys = ["colors", "color_palette", "dominant_colors", "primary_colors"]
            for color_key in color_keys:
                if color_key in metadata:
                    color_data = metadata[color_key]
                    if isinstance(color_data, (list, dict)) and color_data:
                        scene_updates["color_analysis"] = color_data
                        skip_ai["color_analysis"] = True
                        logger.info(f"Scene {scene_id}: Using existing color analysis from HF")
                        break
                        
            # Depth map handling
            depth_keys = ["depth_map", "depth", "depth_image", "depth_data"]
            for depth_key in depth_keys:
                if depth_key in metadata:
                    depth_data = metadata[depth_key]
                    if depth_data:  # Could be base64, URL, or other format
                        scene_updates["depth_available"] = True
                        skip_ai["depth_estimation"] = True
                        logger.info(f"Scene {scene_id}: Found existing depth data in HF metadata")
                        # TODO: Handle actual depth map upload to R2 if needed
                        break
                        
            # Object detection mapping - Enhanced for COCO format and other standards
            objects_keys = ["objects", "annotations", "bounding_boxes", "detections", "instances"]
            for obj_key in objects_keys:
                if obj_key in metadata:
                    objects = metadata[obj_key]
                    if isinstance(objects, list) and objects:
                        # Handle different annotation formats
                        if obj_key == "annotations" and self._is_coco_format(objects):
                            # COCO format: [{bbox: [x,y,w,h], category_id: int, category: str, ...}]
                            converted_objects = self._convert_coco_annotations_to_modomo(objects, scene_id)
                            objects_data.extend(converted_objects)
                        else:
                            # Standard format conversion
                            for i, obj in enumerate(objects):
                                if isinstance(obj, dict):
                                    converted_obj = self._convert_hf_object_to_modomo(obj, i)
                                    if converted_obj:
                                        objects_data.append(converted_obj)
                                    
                        # Apply configuration thresholds and preferences for object detection
                        if (objects_data and 
                            settings.PREFER_EXISTING_ANNOTATIONS and 
                            not settings.FORCE_AI_REPROCESSING):
                            
                            # Filter objects by confidence threshold if enabled
                            filtered_objects = []
                            for obj in objects_data:
                                obj_confidence = obj.get("confidence", 0.8)
                                if obj_confidence >= settings.MIN_OBJECT_CONFIDENCE:
                                    filtered_objects.append(obj)
                                else:
                                    logger.debug(f"Scene {scene_id}: Object below confidence threshold ({obj_confidence:.2f} < {settings.MIN_OBJECT_CONFIDENCE}), excluding")
                            
                            if filtered_objects:
                                objects_data = filtered_objects
                                skip_ai["object_detection"] = True
                                logger.info(f"Scene {scene_id}: Using {len(objects_data)} existing objects from HF ({obj_key} format) after confidence filtering")
                            else:
                                logger.info(f"Scene {scene_id}: No objects meet confidence threshold ({settings.MIN_OBJECT_CONFIDENCE}), will reprocess")
                                objects_data = []
                        elif settings.FORCE_AI_REPROCESSING:
                            logger.info(f"Scene {scene_id}: Force AI reprocessing enabled, ignoring existing objects")
                            objects_data = []
                        break
                        
            # Material detection mapping
            if "materials" in metadata or "material" in metadata:
                materials = metadata.get("materials", [metadata.get("material")])
                if materials:
                    skip_ai["material_classification"] = True
                    logger.info(f"Scene {scene_id}: Found existing material data in HF")
                    
            logger.info(f"Scene {scene_id}: HF metadata processing complete - skip_ai: {skip_ai}")
            
        except Exception as e:
            logger.warning(f"Scene {scene_id}: Error processing HF metadata: {e}")
            # Return safe defaults on error
            scene_updates = {"attrs": metadata}
            
        return {
            "scene_updates": scene_updates,
            "objects_data": objects_data, 
            "skip_ai": skip_ai
        }
    
    def _is_coco_format(self, annotations: List[Dict[str, Any]]) -> bool:
        """
        Detect if annotations follow COCO format.
        
        Args:
            annotations: List of annotation dictionaries
            
        Returns:
            True if COCO format detected, False otherwise
        """
        if not annotations or not isinstance(annotations, list):
            return False
            
        # Check if first annotation has COCO-style fields
        first_annotation = annotations[0]
        if not isinstance(first_annotation, dict):
            return False
            
        # COCO format indicators
        coco_indicators = [
            "category_id" in first_annotation,
            "bbox" in first_annotation and isinstance(first_annotation.get("bbox"), list),
            "area" in first_annotation,
            "id" in first_annotation,
            "image_id" in first_annotation
        ]
        
        # If at least 2 COCO indicators are present, likely COCO format
        return sum(coco_indicators) >= 2
    
    def _convert_coco_annotations_to_modomo(self, coco_annotations: List[Dict[str, Any]], scene_id: str) -> List[Dict[str, Any]]:
        """
        Convert COCO format annotations to Modomo object format.
        
        Args:
            coco_annotations: List of COCO annotation dictionaries
            scene_id: Scene ID for logging
            
        Returns:
            List of Modomo object dictionaries
        """
        modomo_objects = []
        
        # COCO category ID to name mapping (common COCO categories)
        coco_categories = {
            1: "person", 2: "bicycle", 3: "car", 4: "motorcycle", 5: "airplane", 6: "bus", 7: "train", 8: "truck", 9: "boat", 10: "traffic_light",
            11: "fire_hydrant", 13: "stop_sign", 14: "parking_meter", 15: "bench", 16: "bird", 17: "cat", 18: "dog", 19: "horse", 20: "sheep",
            21: "cow", 22: "elephant", 23: "bear", 24: "zebra", 25: "giraffe", 27: "backpack", 28: "umbrella", 31: "handbag", 32: "tie", 33: "suitcase",
            34: "frisbee", 35: "skis", 36: "snowboard", 37: "sports_ball", 38: "kite", 39: "baseball_bat", 40: "baseball_glove", 41: "skateboard", 42: "surfboard", 43: "tennis_racket",
            44: "bottle", 46: "wine_glass", 47: "cup", 48: "fork", 49: "knife", 50: "spoon", 51: "bowl", 52: "banana", 53: "apple", 54: "sandwich",
            55: "orange", 56: "broccoli", 57: "carrot", 58: "hot_dog", 59: "pizza", 60: "donut", 61: "cake", 62: "chair", 63: "couch", 64: "potted_plant",
            65: "bed", 67: "dining_table", 70: "toilet", 72: "tv", 73: "laptop", 74: "mouse", 75: "remote", 76: "keyboard", 77: "cell_phone", 78: "microwave",
            79: "oven", 80: "toaster", 81: "sink", 82: "refrigerator", 84: "book", 85: "clock", 86: "vase", 87: "scissors", 88: "teddy_bear", 89: "hair_drier", 90: "toothbrush"
        }
        
        for i, annotation in enumerate(coco_annotations):
            try:
                # Extract COCO fields
                bbox = annotation.get("bbox", [])
                if not bbox or len(bbox) != 4:
                    logger.warning(f"Scene {scene_id}: Skipping COCO annotation {i} - invalid bbox: {bbox}")
                    continue
                
                # COCO bbox format is [x, y, width, height] - already correct for Modomo
                bbox_normalized = bbox
                
                # Validate bbox if required by configuration
                if settings.REQUIRE_BBOX_VALIDATION:
                    if (bbox_normalized[2] <= 0 or bbox_normalized[3] <= 0 or
                        bbox_normalized[0] < 0 or bbox_normalized[1] < 0):
                        logger.warning(f"Scene {scene_id}: Skipping COCO annotation {i} - invalid bbox: {bbox_normalized}")
                        continue
                
                # Get category name
                category_id = annotation.get("category_id")
                category_name = annotation.get("category") or annotation.get("category_name")
                
                if category_name:
                    category = str(category_name).lower()
                elif category_id and category_id in coco_categories:
                    category = coco_categories[category_id]
                else:
                    category = "object"  # Default fallback
                
                # Map COCO furniture categories to Modomo taxonomy
                furniture_mapping = {
                    "chair": "seating",
                    "couch": "seating", 
                    "bed": "bedroom",
                    "dining_table": "tables",
                    "potted_plant": "decorative",
                    "tv": "electronics",
                    "laptop": "electronics",
                    "refrigerator": "appliances",
                    "microwave": "appliances",
                    "oven": "appliances",
                    "sink": "fixtures",
                    "toilet": "fixtures",
                    "bottle": "accessories",
                    "cup": "accessories",
                    "bowl": "accessories",
                    "vase": "decorative",
                    "clock": "decorative",
                    "book": "accessories"
                }
                
                modomo_category = furniture_mapping.get(category, category)
                
                # Create Modomo object
                confidence = float(annotation.get("score", annotation.get("confidence", 0.9)))
                
                modomo_obj = {
                    "category": modomo_category,
                    "confidence": confidence,
                    "bbox": bbox_normalized,
                    "description": annotation.get("caption", annotation.get("description")),
                    "attributes": {
                        "coco_category_id": category_id,
                        "coco_category_name": category,
                        "coco_area": annotation.get("area"),
                        "coco_id": annotation.get("id"),
                        "coco_iscrowd": annotation.get("iscrowd", 0)
                    }
                }
                
                # Extract enhanced data: segmentation masks (polygon or RLE format)
                if "segmentation" in annotation:
                    segmentation = annotation["segmentation"]
                    if isinstance(segmentation, list):
                        # Polygon format (list of vertex coordinates)
                        modomo_obj["segmentation"] = {
                            "type": "polygon",
                            "data": segmentation
                        }
                    elif isinstance(segmentation, dict):
                        # RLE (Run-Length Encoding) format
                        modomo_obj["segmentation"] = {
                            "type": "rle",
                            "data": segmentation
                        }
                elif "segmentation_polygon" in annotation:
                    modomo_obj["segmentation"] = {
                        "type": "polygon",
                        "data": annotation["segmentation_polygon"]
                    }
                elif "segmentation_rle" in annotation:
                    modomo_obj["segmentation"] = {
                        "type": "rle",
                        "data": annotation["segmentation_rle"]
                    }
                
                # Extract keypoints for pose estimation
                if "keypoints" in annotation:
                    # COCO keypoints format: [x1, y1, v1, x2, y2, v2, ...]
                    # where v is visibility flag (0: not labeled, 1: labeled but not visible, 2: labeled and visible)
                    keypoints = annotation["keypoints"]
                    if keypoints and isinstance(keypoints, list) and len(keypoints) % 3 == 0:
                        modomo_obj["keypoints"] = {
                            "points": keypoints,
                            "num_keypoints": annotation.get("num_keypoints", len(keypoints) // 3)
                        }
                
                # Extract instance-specific attributes
                if "attributes" in annotation:
                    modomo_obj["instance_attributes"] = annotation["attributes"]
                
                # Extract custom metadata fields (material, color, style, etc.)
                custom_fields = ["material", "color", "style", "condition", "brand", "model", "finish"]
                for field in custom_fields:
                    if field in annotation:
                        modomo_obj["attributes"][field] = annotation[field]
                
                # Filter out None values from attributes
                modomo_obj["attributes"] = {k: v for k, v in modomo_obj["attributes"].items() if v is not None}
                
                modomo_objects.append(modomo_obj)
                
                logger.debug(f"Scene {scene_id}: Converted COCO annotation {i}: {category} -> {modomo_category}")
                
            except Exception as e:
                logger.warning(f"Scene {scene_id}: Failed to convert COCO annotation {i}: {e}")
                continue
        
        logger.info(f"Scene {scene_id}: Successfully converted {len(modomo_objects)} COCO annotations to Modomo format")
        return modomo_objects
    
    def _convert_hf_object_to_modomo(self, hf_obj: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """
        Convert HF object annotation to Modomo object format.
        
        Args:
            hf_obj: HF object dictionary 
            index: Object index for ID generation
            
        Returns:
            Modomo object dictionary or None if conversion fails
        """
        try:
            # Extract category/label
            category = hf_obj.get("category", hf_obj.get("label", hf_obj.get("class", "furniture")))
            
            # Extract bounding box - handle multiple formats
            bbox = hf_obj.get("bbox", hf_obj.get("bounding_box", hf_obj.get("box")))
            if not bbox:
                return None
                
            # Normalize bbox format to [x, y, width, height]
            if isinstance(bbox, list) and len(bbox) == 4:
                if "x1" in str(hf_obj) or "x2" in str(hf_obj):  # [x1, y1, x2, y2] format
                    x1, y1, x2, y2 = bbox
                    bbox_normalized = [x1, y1, x2-x1, y2-y1]
                else:  # Already [x, y, w, h] format
                    bbox_normalized = bbox
            elif isinstance(bbox, dict):
                x = bbox.get("x", bbox.get("x1", 0))
                y = bbox.get("y", bbox.get("y1", 0)) 
                w = bbox.get("width", bbox.get("w", bbox.get("x2", 0) - x))
                h = bbox.get("height", bbox.get("h", bbox.get("y2", 0) - y))
                bbox_normalized = [x, y, w, h]
            else:
                return None
                
            # Validate bbox if required by configuration
            if settings.REQUIRE_BBOX_VALIDATION:
                if (bbox_normalized[2] <= 0 or bbox_normalized[3] <= 0 or
                    bbox_normalized[0] < 0 or bbox_normalized[1] < 0):
                    logger.warning(f"HF object {index}: Invalid bbox dimensions: {bbox_normalized}, skipping")
                    return None
                
            # Create Modomo object
            modomo_obj = {
                "category": str(category).lower(),
                "confidence": float(hf_obj.get("confidence", hf_obj.get("score", 0.8))),
                "bbox": bbox_normalized,
                "description": hf_obj.get("description", hf_obj.get("caption")),
                "attributes": {}
            }
            
            # Add additional attributes 
            for key, value in hf_obj.items():
                if key not in ["category", "label", "class", "bbox", "bounding_box", "box", "confidence", "score"]:
                    modomo_obj["attributes"][key] = value
                    
            return modomo_obj
            
        except Exception as e:
            logger.warning(f"Failed to convert HF object {index}: {e}")
            return None