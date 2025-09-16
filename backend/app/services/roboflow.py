"""
Roboflow dataset import service
"""

import logging
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

try:
    import roboflow
    from roboflow import Roboflow
    ROBOFLOW_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Roboflow dependencies not available: {e}")
    ROBOFLOW_AVAILABLE = False
    roboflow = None
    Roboflow = None

import requests
from PIL import Image
import io
import uuid

from app.core.config import settings
from app.services.storage import StorageService
from app.services.datasets import DatasetService
from app.schemas.dataset import SceneCreate

logger = logging.getLogger(__name__)

class RoboflowService:
    """Service for importing datasets from Roboflow Universe"""
    
    # Roboflow Universe URL pattern: universe.roboflow.com/{workspace}/{project}/model/{version}
    ROBOFLOW_URL_PATTERN = re.compile(r'^https://universe\.roboflow\.com/([\w-]+)/([\w-]+)(?:/model/(\d+))?(?:/.*)?$')
    
    def __init__(self):
        self.storage = StorageService()
        self.dataset_service = DatasetService()
        self.rf_client = None
        
    def _init_client(self, api_key: str) -> bool:
        """Initialize Roboflow client with API key"""
        if not ROBOFLOW_AVAILABLE:
            logger.error("Roboflow SDK not available")
            return False
            
        try:
            self.rf_client = Roboflow(api_key=api_key)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Roboflow client: {e}")
            return False
    
    def validate_roboflow_url(self, url: str) -> Optional[tuple[str, str, Optional[str]]]:
        """
        Validate Roboflow Universe URL and extract workspace/project/version.
        
        Args:
            url: Roboflow Universe dataset URL
            
        Returns:
            Tuple of (workspace, project, version) if valid, None otherwise
            
        Example:
            >>> svc = RoboflowService()
            >>> svc.validate_roboflow_url("https://universe.roboflow.com/roboflow-100/furniture-ngpea/model/1")
            ('roboflow-100', 'furniture-ngpea', '1')
        """
        match = self.ROBOFLOW_URL_PATTERN.match(url)
        if not match:
            return None
            
        workspace, project, version = match.groups()
        return (workspace, project, version or "1")  # Default to version 1
    
    def extract_dataset_info(self, roboflow_url: str, api_key: str) -> Dict[str, Any]:
        """
        Extract basic metadata from Roboflow dataset.
        
        Args:
            roboflow_url: Roboflow Universe dataset URL
            api_key: Roboflow API key
            
        Returns:
            Dictionary with dataset info or empty dict on error
        """
        if not ROBOFLOW_AVAILABLE:
            logger.warning("Roboflow dependencies not available")
            return {}
            
        try:
            url_parts = self.validate_roboflow_url(roboflow_url)
            if not url_parts:
                return {}
                
            workspace, project, version = url_parts
            
            if not self._init_client(api_key):
                return {}
            
            # Get workspace and project
            rf_workspace = self.rf_client.workspace(workspace)
            rf_project = rf_workspace.project(project)
            rf_version = rf_project.version(int(version))
            
            return {
                "workspace": workspace,
                "project": project,
                "version": version,
                "dataset_id": f"{workspace}/{project}/v{version}",
                "description": f"Roboflow dataset: {workspace}/{project} version {version}",
                "tags": ["roboflow", "object_detection", "furniture"],
                "license": "varies",  # Roboflow datasets have various licenses
                "format": "coco"  # Roboflow typically exports in COCO format
            }
            
        except Exception as e:
            logger.warning(f"Failed to extract Roboflow dataset info from {roboflow_url}: {e}")
            return {}
    
    def load_roboflow_dataset_images(
        self, 
        roboflow_url: str, 
        api_key: str,
        export_format: str = "coco",
        max_images: Optional[int] = None,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Download and load images from Roboflow dataset with annotations.
        
        Args:
            roboflow_url: Roboflow Universe dataset URL
            api_key: Roboflow API key
            export_format: Export format (coco, yolov8, etc.)
            max_images: Maximum images to process (None for all)
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of image records with metadata and annotations
            
        Example:
            >>> svc = RoboflowService()
            >>> images = svc.load_roboflow_dataset_images(
            ...     "https://universe.roboflow.com/roboflow-100/furniture-ngpea/model/1",
            ...     "your_api_key"
            ... )
            >>> len(images) > 0
            True
        """
        if not ROBOFLOW_AVAILABLE:
            logger.error("Roboflow dependencies not available")
            return []
            
        import time
        
        for attempt in range(max_retries):
            try:
                url_parts = self.validate_roboflow_url(roboflow_url)
                if not url_parts:
                    logger.error(f"Invalid Roboflow URL: {roboflow_url}")
                    return []
                    
                workspace, project, version = url_parts
                
                if not self._init_client(api_key):
                    logger.error("Failed to initialize Roboflow client")
                    return []
                
                logger.info(f"Loading Roboflow dataset {workspace}/{project} v{version} (attempt {attempt + 1})")
                
                # Get workspace, project, and version
                rf_workspace = self.rf_client.workspace(workspace)
                rf_project = rf_workspace.project(project)
                rf_version = rf_project.version(int(version))
                
                # Download dataset
                dataset = rf_version.download(export_format, location="./temp_roboflow")
                
                if not dataset or not hasattr(dataset, 'location'):
                    logger.error(f"Failed to download dataset from Roboflow")
                    return []
                
                dataset_path = dataset.location
                logger.info(f"Downloaded Roboflow dataset to {dataset_path}")
                
                # Parse annotations and images
                images = self._parse_roboflow_dataset(dataset_path, export_format, max_images)
                
                # Cleanup temporary files
                self._cleanup_temp_files(dataset_path)
                
                logger.info(f"Successfully loaded {len(images)} images from Roboflow dataset")
                return images
                
            except Exception as e:
                logger.warning(f"Roboflow dataset loading attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    # Exponential backoff: wait 2, 4, 8 seconds
                    wait_time = 2 ** (attempt + 1)
                    logger.info(f"Retrying Roboflow dataset load in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to load Roboflow dataset {roboflow_url} after {max_retries} attempts")
                    return []
        
        return []
    
    def _parse_roboflow_dataset(self, dataset_path: str, export_format: str, max_images: Optional[int]) -> List[Dict[str, Any]]:
        """Parse downloaded Roboflow dataset and extract images with annotations"""
        images = []
        
        try:
            if export_format.lower() == "coco":
                images = self._parse_coco_dataset(dataset_path, max_images)
            elif export_format.lower().startswith("yolo"):
                images = self._parse_yolo_dataset(dataset_path, max_images)
            else:
                logger.warning(f"Unsupported export format: {export_format}")
                
        except Exception as e:
            logger.error(f"Failed to parse Roboflow dataset: {e}")
            
        return images
    
    def _parse_coco_dataset(self, dataset_path: str, max_images: Optional[int]) -> List[Dict[str, Any]]:
        """Parse COCO format Roboflow dataset"""
        images = []
        
        try:
            # Look for COCO annotation files
            import glob
            annotation_files = glob.glob(os.path.join(dataset_path, "*", "_annotations.coco.json"))
            
            if not annotation_files:
                logger.warning("No COCO annotation files found in Roboflow dataset")
                return []
            
            # Use train split if available, otherwise use first found
            train_annotation = None
            for ann_file in annotation_files:
                if "train" in ann_file:
                    train_annotation = ann_file
                    break
            
            annotation_file = train_annotation or annotation_files[0]
            logger.info(f"Using COCO annotation file: {annotation_file}")
            
            # Load COCO annotations
            with open(annotation_file, 'r') as f:
                coco_data = json.load(f)
            
            # Get images directory
            images_dir = os.path.dirname(annotation_file)
            
            # Create category mapping
            categories = {cat['id']: cat['name'] for cat in coco_data.get('categories', [])}
            
            # Process images with annotations
            coco_images = coco_data.get('images', [])
            coco_annotations = coco_data.get('annotations', [])
            
            # Group annotations by image ID
            annotations_by_image = {}
            for ann in coco_annotations:
                image_id = ann['image_id']
                if image_id not in annotations_by_image:
                    annotations_by_image[image_id] = []
                annotations_by_image[image_id].append(ann)
            
            # Process each image
            for idx, coco_image in enumerate(coco_images):
                if max_images and idx >= max_images:
                    break
                
                image_path = os.path.join(images_dir, coco_image['file_name'])
                if not os.path.exists(image_path):
                    logger.warning(f"Image not found: {image_path}")
                    continue
                
                # Load PIL image
                try:
                    pil_image = Image.open(image_path)
                    width, height = pil_image.size
                    
                    # Get annotations for this image
                    image_annotations = annotations_by_image.get(coco_image['id'], [])
                    
                    # Convert annotations to standard format
                    converted_annotations = []
                    for ann in image_annotations:
                        category_name = categories.get(ann['category_id'], 'furniture')
                        converted_ann = {
                            'bbox': ann['bbox'],  # COCO format: [x, y, width, height]
                            'category': category_name,
                            'category_id': ann['category_id'],
                            'confidence': ann.get('score', 1.0),
                            'area': ann.get('area'),
                            'id': ann.get('id'),
                            'iscrowd': ann.get('iscrowd', 0)
                        }
                        converted_annotations.append(converted_ann)
                    
                    images.append({
                        "image": pil_image,
                        "width": width,
                        "height": height,
                        "roboflow_index": idx,
                        "filename": coco_image['file_name'],
                        "metadata": {
                            "image_id": coco_image['id'],
                            "annotations": converted_annotations,
                            "coco_format": True
                        }
                    })
                    
                    if idx % 10 == 0:
                        logger.info(f"Processed {idx + 1} images from Roboflow dataset")
                        
                except Exception as e:
                    logger.warning(f"Failed to process image {image_path}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to parse COCO dataset: {e}")
            
        return images
    
    def _parse_yolo_dataset(self, dataset_path: str, max_images: Optional[int]) -> List[Dict[str, Any]]:
        """Parse YOLO format Roboflow dataset"""
        # TODO: Implement YOLO format parsing if needed
        logger.warning("YOLO format parsing not yet implemented for Roboflow datasets")
        return []
    
    def _cleanup_temp_files(self, dataset_path: str):
        """Clean up temporary dataset files"""
        try:
            import shutil
            if os.path.exists(dataset_path):
                shutil.rmtree(dataset_path)
                logger.debug(f"Cleaned up temporary dataset files: {dataset_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary files {dataset_path}: {e}")
    
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
    
    def handle_existing_roboflow_metadata(self, metadata: Dict[str, Any], scene_id: str, roboflow_index: int) -> Dict[str, Any]:
        """
        Enhanced metadata processing for Roboflow datasets to avoid redundant AI processing.
        
        This method intelligently detects existing high-quality annotations and metadata
        from Roboflow datasets and determines which AI components can be skipped to 
        improve processing efficiency and reduce costs.
        
        Args:
            metadata: Raw Roboflow dataset item metadata 
            scene_id: Database scene ID 
            roboflow_index: Original Roboflow dataset index
            
        Returns:
            Dict with keys:
            - scene_updates: Dict of updates to apply to scene record
            - objects_data: List of object records to create (if any)
            - skip_ai: Dict indicating which AI components to skip
            
        Example:
            >>> result = svc.handle_existing_roboflow_metadata({
            ...     "annotations": [...], "room_type": "living_room"
            ... }, "scene_123", 0)
            >>> result["skip_ai"]["object_detection"] 
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
        
        # Configuration-based preferences
        prefer_existing = getattr(settings, 'PREFER_EXISTING_ANNOTATIONS', True)
        min_scene_confidence = getattr(settings, 'MIN_SCENE_CONFIDENCE', 0.7)
        min_object_confidence = getattr(settings, 'MIN_OBJECT_CONFIDENCE', 0.6)
        min_style_confidence = getattr(settings, 'MIN_STYLE_CONFIDENCE', 0.6)
        require_bbox_validation = getattr(settings, 'REQUIRE_BBOX_VALIDATION', True)
        force_reprocessing = getattr(settings, 'FORCE_AI_REPROCESSING', False)
        
        # Preserve all original metadata in attrs
        scene_updates["attrs"] = {
            **metadata,
            "roboflow_original_index": roboflow_index,
            "metadata_processed_at": datetime.utcnow().isoformat(),
            "enhanced_pipeline_version": "1.0"
        }
        
        # Force reprocessing override
        if force_reprocessing:
            logger.info(f"Scene {scene_id}: Force reprocessing enabled - skipping metadata optimization")
            return {
                "scene_updates": scene_updates,
                "objects_data": objects_data,
                "skip_ai": skip_ai
            }
        
        try:
            # 1. SCENE CLASSIFICATION - Look for room type information
            room_info = self._extract_roboflow_room_info(metadata)
            if room_info and prefer_existing:
                confidence = room_info.get('confidence', 0.0)
                if confidence >= min_scene_confidence:
                    scene_updates.update({
                        "scene_type": room_info['room_type'],
                        "scene_conf": confidence
                    })
                    skip_ai["scene_classification"] = True
                    logger.info(f"Scene {scene_id}: Using existing room classification: {room_info['room_type']} (conf: {confidence:.2f})")
            
            # 2. STYLE ANALYSIS - Look for style metadata
            style_info = self._extract_roboflow_style_info(metadata)
            if style_info and prefer_existing:
                confidence = style_info.get('confidence', 0.0)
                if confidence >= min_style_confidence:
                    scene_updates.update({
                        "primary_style": style_info['style'],
                        "style_confidence": confidence
                    })
                    skip_ai["style_analysis"] = True
                    logger.info(f"Scene {scene_id}: Using existing style classification: {style_info['style']} (conf: {confidence:.2f})")
            
            # 3. COLOR ANALYSIS - Look for color palette information
            color_info = self._extract_roboflow_color_info(metadata)
            if color_info and prefer_existing:
                scene_updates["color_analysis"] = color_info
                skip_ai["color_analysis"] = True
                logger.info(f"Scene {scene_id}: Using existing color analysis with {len(color_info.get('dominant_colors', []))} colors")
            
            # 4. OBJECT DETECTION - Process existing annotations
            annotations = metadata.get("annotations", [])
            if annotations and isinstance(annotations, list) and prefer_existing:
                # Convert Roboflow annotations to Modomo format
                from app.services.huggingface import HuggingFaceService
                hf_service = HuggingFaceService()
                
                # Check if COCO format and use enhanced conversion
                if hf_service._is_coco_format(annotations):
                    logger.info(f"Scene {scene_id}: Detected COCO format Roboflow dataset")
                    objects_data = hf_service._convert_coco_annotations_to_modomo(annotations, scene_id)
                else:
                    # Standard Roboflow annotation conversion
                    logger.info(f"Scene {scene_id}: Processing standard Roboflow annotations")
                    for i, annotation in enumerate(annotations):
                        if isinstance(annotation, dict):
                            converted_obj = self._convert_roboflow_object_to_modomo(annotation, i)
                            if converted_obj and converted_obj.get('confidence', 0) >= min_object_confidence:
                                # Additional bbox validation if required
                                if require_bbox_validation:
                                    bbox = converted_obj.get('bbox', [])
                                    if len(bbox) == 4 and all(isinstance(x, (int, float)) and x >= 0 for x in bbox) and bbox[2] > 0 and bbox[3] > 0:
                                        objects_data.append(converted_obj)
                                    else:
                                        logger.warning(f"Scene {scene_id}: Skipping object {i} due to invalid bbox: {bbox}")
                                else:
                                    objects_data.append(converted_obj)
                
                if objects_data:
                    skip_ai["object_detection"] = True
                    avg_confidence = sum(obj.get('confidence', 0) for obj in objects_data) / len(objects_data)
                    logger.info(f"Scene {scene_id}: Using {len(objects_data)} existing objects from Roboflow (avg conf: {avg_confidence:.2f})")
                    
                    # If we have high-quality object data, also skip material classification for those objects
                    high_conf_objects = [obj for obj in objects_data if obj.get('confidence', 0) >= 0.8]
                    if len(high_conf_objects) >= len(objects_data) * 0.7:  # 70% of objects are high confidence
                        skip_ai["material_classification"] = True
                        logger.info(f"Scene {scene_id}: Skipping material classification due to {len(high_conf_objects)} high-confidence objects")
            
            # Calculate efficiency gains
            skipped_components = [k for k, v in skip_ai.items() if v]
            efficiency_gain = len(skipped_components) / len(skip_ai) * 100
            
            logger.info(f"Scene {scene_id}: Enhanced Roboflow processing complete - {len(skipped_components)}/6 components skipped ({efficiency_gain:.1f}% efficiency gain)")
            
        except Exception as e:
            logger.warning(f"Scene {scene_id}: Error in enhanced Roboflow metadata processing: {e}")
            # Return safe defaults on error but preserve metadata
            scene_updates = {"attrs": metadata}
            
        return {
            "scene_updates": scene_updates,
            "objects_data": objects_data, 
            "skip_ai": skip_ai
        }
    
    def _extract_roboflow_room_info(self, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract room type information from Roboflow metadata"""
        # Look for common room type fields in Roboflow datasets
        room_fields = [
            'room_type', 'room', 'space_type', 'area_type', 'scene_type',
            'room_category', 'interior_type', 'space_category'
        ]
        
        for field in room_fields:
            if field in metadata:
                room_value = metadata[field]
                confidence_field = f"{field}_confidence"
                confidence = metadata.get(confidence_field, 0.8)  # Default confidence
                
                if isinstance(room_value, str):
                    return {
                        'room_type': room_value.lower().strip(),
                        'confidence': float(confidence)
                    }
        
        return None
    
    def _extract_roboflow_style_info(self, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract design style information from Roboflow metadata"""
        # Look for style fields in Roboflow datasets
        style_fields = [
            'style', 'design_style', 'interior_style', 'decor_style',
            'aesthetic', 'theme', 'design_theme'
        ]
        
        for field in style_fields:
            if field in metadata:
                style_value = metadata[field]
                confidence_field = f"{field}_confidence"
                confidence = metadata.get(confidence_field, 0.7)  # Default confidence
                
                if isinstance(style_value, str):
                    return {
                        'style': style_value.lower().strip(),
                        'confidence': float(confidence)
                    }
        
        return None
    
    def _extract_roboflow_color_info(self, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract color information from Roboflow metadata"""
        # Look for color fields in Roboflow datasets
        color_fields = [
            'colors', 'dominant_colors', 'color_palette', 'primary_colors',
            'main_colors', 'color_scheme'
        ]
        
        for field in color_fields:
            if field in metadata:
                color_value = metadata[field]
                
                if isinstance(color_value, list) and len(color_value) > 0:
                    return {
                        'dominant_colors': color_value,
                        'color_count': len(color_value),
                        'source': 'roboflow_metadata'
                    }
                elif isinstance(color_value, str):
                    # Single color as string
                    return {
                        'dominant_colors': [color_value],
                        'color_count': 1,
                        'source': 'roboflow_metadata'
                    }
        
        return None
    
    def _convert_roboflow_object_to_modomo(self, roboflow_obj: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """
        Convert Roboflow object annotation to Modomo object format.
        
        Args:
            roboflow_obj: Roboflow object dictionary 
            index: Object index for ID generation
            
        Returns:
            Modomo object dictionary or None if conversion fails
        """
        try:
            # Extract category/label
            category = roboflow_obj.get("category", roboflow_obj.get("class", roboflow_obj.get("label", "furniture")))
            
            # Extract bounding box - Roboflow typically uses COCO format [x, y, width, height]
            bbox = roboflow_obj.get("bbox", roboflow_obj.get("bounding_box", roboflow_obj.get("box")))
            if not bbox:
                return None
                
            # Normalize bbox format to [x, y, width, height]
            if isinstance(bbox, list) and len(bbox) == 4:
                bbox_normalized = bbox  # Assume already in correct format
            else:
                return None
                
            # Create Modomo object
            modomo_obj = {
                "category": str(category).lower(),
                "confidence": float(roboflow_obj.get("confidence", roboflow_obj.get("score", 0.9))),
                "bbox": bbox_normalized,
                "description": roboflow_obj.get("description", roboflow_obj.get("caption")),
                "attributes": {}
            }
            
            # Add additional attributes 
            for key, value in roboflow_obj.items():
                if key not in ["category", "class", "label", "bbox", "bounding_box", "box", "confidence", "score"]:
                    modomo_obj["attributes"][key] = value
                    
            return modomo_obj
            
        except Exception as e:
            logger.warning(f"Failed to convert Roboflow object {index}: {e}")
            return None