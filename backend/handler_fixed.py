"""
Production RunPod Handler for Modomo AI Pipeline
Handles interior design scene analysis with YOLO, CLIP, SAM2, and depth estimation
"""

import runpod
import base64
import io
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import torch
import numpy as np

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced fallback functions for RunPod environment (no app module dependency)
def get_canonical_label(label: str) -> str:
    """Convert label to canonical form"""
    return label.lower().replace(' ', '_').replace('-', '_')

def get_category_for_item(item: str) -> str:
    """Map item to category"""
    item_lower = item.lower()
    if item_lower in ['chair', 'stool', 'bench', 'sofa', 'couch', 'loveseat', 'sectional']:
        return 'seating'
    elif item_lower in ['table', 'desk', 'coffee_table', 'dining_table']:
        return 'tables'
    elif item_lower in ['bed', 'mattress', 'headboard']:
        return 'bedroom'
    elif item_lower in ['cabinet', 'dresser', 'bookshelf', 'shelf']:
        return 'storage'
    elif item_lower in ['lamp', 'light', 'chandelier']:
        return 'lighting'
    else:
        return 'furniture'

def get_yolo_whitelist() -> set:
    """Get expanded furniture items for YOLO filtering"""
    return {
        # Seating
        'chair', 'couch', 'sofa', 'bench', 'stool', 'ottoman', 'sectional', 
        'loveseat', 'recliner', 'armchair', 'bar_stool', 'office_chair',
        
        # Tables  
        'table', 'desk', 'coffee_table', 'dining_table', 'side_table',
        'end_table', 'nightstand', 'console_table',
        
        # Storage
        'cabinet', 'dresser', 'bookshelf', 'shelf', 'wardrobe', 'armoire',
        'tv_stand', 'media_console', 'chest_of_drawers', 'filing_cabinet',
        
        # Bedroom
        'bed', 'mattress', 'headboard', 'bed_frame',
        
        # Lighting & Electronics
        'lamp', 'floor_lamp', 'table_lamp', 'ceiling_light', 'chandelier',
        'tv', 'television', 'monitor', 'computer',
        
        # Kitchen
        'refrigerator', 'fridge', 'stove', 'oven', 'microwave', 'dishwasher',
        'kitchen_island', 'sink',
        
        # Bathroom
        'toilet', 'bathtub', 'shower', 'bathroom_sink',
        
        # Decor & Accessories
        'mirror', 'plant', 'vase', 'rug', 'carpet', 'curtain', 'curtains',
        'pillow', 'cushion', 'picture', 'painting', 'frame',
        
        # Architectural
        'door', 'window', 'fireplace'
    }

def is_furniture_item(label: str, confidence: float = 0.0, min_conf: float = 0.35) -> bool:
    """Check if detected item is furniture"""
    return label.lower() in get_yolo_whitelist() and confidence >= min_conf


# Global model storage
models = {}
model_loading_lock = False

def load_models():
    """Load all AI models into memory (called once on cold start)"""
    global models, model_loading_lock
    
    if model_loading_lock:
        logger.info("Models already loading...")
        return False
        
    if models:
        logger.info("Models already loaded")
        return True
        
    model_loading_lock = True
    
    try:
        logger.info("🔄 Loading Modomo AI models...")
        start_time = time.time()
        
        # Check GPU availability and set device
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🎯 Using device: {device}")
        
        if torch.cuda.is_available():
            logger.info(f"🚀 GPU detected: {torch.cuda.get_device_name(0)}")
            logger.info(f"💾 GPU memory: {torch.cuda.get_device_properties(0).total_memory // (1024**3)}GB")
        else:
            logger.warning("⚠️ No GPU available, using CPU")
        
        # Load CLIP for scene classification and style analysis
        logger.info("Loading CLIP model...")
        from transformers import CLIPProcessor, CLIPModel
        models['clip_model'] = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
        models['clip_processor'] = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        logger.info(f"✅ CLIP loaded on {device}")
        
        # Load YOLO for object detection  
        logger.info("Loading YOLO model...")
        from ultralytics import YOLO
        models['yolo'] = YOLO('yolov8n.pt')  # Nano version for speed
        if torch.cuda.is_available():
            models['yolo'].to(device)
        logger.info(f"✅ YOLO loaded on {device}")
        
        # Load SAM2 for segmentation
        logger.info("Loading SAM2 model...")
        try:
            from sam2.build_sam import build_sam2
            from sam2.sam2_image_predictor import SAM2ImagePredictor

            logger.info(f"Loading SAM2 on device: {device}")

            # Use the correct SAM2 model loading
            sam2_checkpoint = "facebook/sam2-hiera-large"
            sam2_model_cfg = "sam2_hiera_l.yaml"

            # Build the model properly
            sam2_model = build_sam2(sam2_model_cfg, sam2_checkpoint, device=device)
            models['sam2_predictor'] = SAM2ImagePredictor(sam2_model)

            logger.info(f"✅ SAM2 loaded successfully on {device}")

        except Exception as e:
            logger.error(f"SAM2 loading failed: {e}")
            # Try alternative loading method
            try:
                logger.info("Trying alternative SAM2 loading method...")
                from transformers import Sam2Model, Sam2Processor

                models['sam2_model'] = Sam2Model.from_pretrained("facebook/sam2-hiera-large").to(device)
                models['sam2_processor'] = Sam2Processor.from_pretrained("facebook/sam2-hiera-large")
                models['sam2_predictor'] = "transformers_sam2"  # Flag for different method

                logger.info(f"✅ SAM2 loaded via transformers on {device}")

            except Exception as e2:
                logger.error(f"Both SAM2 loading methods failed: {e2}")
                raise Exception(f"SAM2 loading failed: {e}, {e2}")
        
        # Load depth estimation model
        logger.info("Loading depth estimation...")
        from transformers import pipeline
        models['depth'] = pipeline(
            "depth-estimation", 
            model="Intel/dpt-large",
            device=0 if torch.cuda.is_available() else -1
        )
        logger.info(f"✅ Depth estimation loaded on {'GPU' if torch.cuda.is_available() else 'CPU'}")
        
        # Store device for later use
        models['device'] = device
        
        load_time = time.time() - start_time
        logger.info(f"🎉 All models loaded successfully in {load_time:.1f}s")
        model_loading_lock = False
        return True
        
    except Exception as e:
        logger.error(f"❌ Model loading failed: {e}")
        model_loading_lock = False
        models.clear()  # Clear partial state
        return False

def classify_scene(image: Image.Image) -> dict:
    """Classify scene type using CLIP"""
    try:
        scene_types = [
            "a bedroom interior", "a living room interior", "a kitchen interior", 
            "a bathroom interior", "a dining room interior", "an office interior",
            "a hallway interior", "an outdoor patio", "a garage interior"
        ]
        
        inputs = models['clip_processor'](
            text=scene_types, 
            images=[image],  # CLIP processor expects a list of images
            return_tensors="pt", 
            padding=True
        )
        
        # Move inputs to same device as model with error handling
        device = models.get('device', 'cpu')
        try:
            inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
            logger.debug(f"Scene classification inputs moved to device {device}")
        except Exception as e:
            logger.error(f"Error moving scene inputs to device {device}: {e}")
            # Fallback to CPU
            device = 'cpu'
            inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = models['clip_model'](**inputs)
            logits = outputs.logits_per_image
            probs = logits.softmax(dim=1)
        
        # Get top prediction
        best_idx = probs.argmax().item()
        confidence = probs[0][best_idx].item()
        scene_type = scene_types[best_idx].replace("a ", "").replace("an ", "").replace(" interior", "")
        
        # Get top 3 alternatives
        top_indices = probs[0].argsort(descending=True)[:3]
        alternatives = []
        for idx in top_indices:
            alternatives.append({
                "type": scene_types[idx].replace("a ", "").replace("an ", "").replace(" interior", ""),
                "confidence": float(probs[0][idx])
            })
        
        return {
            "scene_type": scene_type,
            "confidence": float(confidence),
            "alternatives": alternatives
        }
        
    except Exception as e:
        logger.error(f"Scene classification failed: {e}")
        return {
            "scene_type": "unknown",
            "confidence": 0.0,
            "alternatives": []
        }

def detect_objects(image: Image.Image) -> list:
    """Detect objects using enhanced YOLO with multi-scale detection"""
    try:
        # Convert PIL to numpy for YOLO
        img_array = np.array(image)
        
        # Multi-scale detection for better coverage
        all_detections = []
        
        # Scale 1: Original size with enhanced parameters
        results = models['yolo'](
            img_array, 
            conf=0.15,          # Lower threshold to catch more objects
            iou=0.45,           # Better NMS threshold
            agnostic_nms=True,  # Class-agnostic NMS for better results
            max_det=50,         # Allow more detections
            verbose=False
        )
        all_detections.extend(_extract_yolo_detections(results, image.size))
        
        # Scale 2: Larger scale for small objects (if image is large enough)
        if image.size[0] > 800 and image.size[1] > 600:
            scale_factor = 1.5
            scaled_size = (int(image.size[0] * scale_factor), int(image.size[1] * scale_factor))
            scaled_image = image.resize(scaled_size, Image.Resampling.BICUBIC)
            scaled_array = np.array(scaled_image)
            
            scaled_results = models['yolo'](
                scaled_array,
                conf=0.18,
                iou=0.5,
                agnostic_nms=True,
                max_det=30,
                verbose=False
            )
            
            # Scale back detections to original coordinates
            scaled_detections = _extract_yolo_detections(scaled_results, scaled_image.size)
            for det in scaled_detections:
                det['bbox'][0] = int(det['bbox'][0] / scale_factor)  # x
                det['bbox'][1] = int(det['bbox'][1] / scale_factor)  # y
                det['bbox'][2] = int(det['bbox'][2] / scale_factor)  # width
                det['bbox'][3] = int(det['bbox'][3] / scale_factor)  # height
                det['area'] = int(det['bbox'][2] * det['bbox'][3])
            
            all_detections.extend(scaled_detections)
        
        # Combine and filter all detections
        return _combine_multi_scale_detections(all_detections)
        
    except Exception as e:
        logger.error(f"Enhanced object detection failed: {e}")
        return []

def _extract_yolo_detections(results, image_size) -> list:
    """Extract and filter detections from YOLO results"""
    objects = []
    
    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                # Extract box data with validation
                coords = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = coords[0], coords[1], coords[2], coords[3]
                
                # Validate coordinates to prevent negative dimensions
                x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
                
                # Ensure x2 > x1 and y2 > y1 (swap if necessary)
                if x2 < x1:
                    x1, x2 = x2, x1
                if y2 < y1:
                    y1, y2 = y2, y1
                
                # Validate minimum dimensions (at least 1 pixel)
                if (x2 - x1) < 1 or (y2 - y1) < 1:
                    continue
                
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                label = models['yolo'].names[cls]
                
                # Enhanced filtering with adaptive confidence thresholds
                canonical_label = get_canonical_label(label)
                is_known_furniture = canonical_label in get_yolo_whitelist()
                
                # Adaptive confidence based on object type and knowledge
                min_conf_threshold = 0.20 if is_known_furniture else 0.35
                
                if is_furniture_item(label, conf, min_conf=min_conf_threshold):
                    # Convert to [x, y, width, height] format
                    bbox_x = int(x1)
                    bbox_y = int(y1)
                    bbox_width = int(x2 - x1)
                    bbox_height = int(y2 - y1)
                    
                    # Double-check dimensions are positive
                    if bbox_width <= 0 or bbox_height <= 0:
                        continue
                    
                    # Use centralized canonical label mapping
                    object_category = get_category_for_item(canonical_label)
                    
                    objects.append({
                        "label": canonical_label,
                        "category": object_category,
                        "confidence": round(conf, 3),
                        "bbox": [bbox_x, bbox_y, bbox_width, bbox_height],
                        "bbox_format": "xywh",
                        "area": int(bbox_width * bbox_height)

                    })
    
    return objects

def _combine_multi_scale_detections(all_detections: list) -> list:
    """Combine detections from multiple scales, removing duplicates"""
    if not all_detections:
        return []
    
    # Enhanced post-processing and filtering
    # Remove very small objects (likely noise)
    objects = [obj for obj in all_detections if obj['area'] >= 100]
    
    # Apply NMS-like filtering for overlapping objects
    objects = _filter_overlapping_objects(objects, iou_threshold=0.4)  # Slightly lower threshold for multi-scale
    
    # Sort by confidence and area (larger objects preferred for same confidence)
    objects.sort(key=lambda x: (x['confidence'], x['area']), reverse=True)
    return objects[:30]  # Increased limit for better coverage

def _filter_overlapping_objects(objects: list, iou_threshold: float = 0.5) -> list:
    """Remove highly overlapping objects of the same type (custom NMS)"""
    if len(objects) <= 1:
        return objects
    
    # Sort by confidence (highest first)
    sorted_objects = sorted(objects, key=lambda x: x['confidence'], reverse=True)
    kept_objects = []
    
    for current_obj in sorted_objects:
        should_keep = True
        current_bbox = current_obj['bbox']  # [x, y, width, height]
        
        for kept_obj in kept_objects:
            # Only check overlap for same object type
            if current_obj['label'] == kept_obj['label']:
                kept_bbox = kept_obj['bbox']
                
                # Calculate IoU between bboxes
                iou = _calculate_bbox_iou(current_bbox, kept_bbox)
                
                if iou > iou_threshold:
                    should_keep = False
                    break
        
        if should_keep:
            kept_objects.append(current_obj)
    
    return kept_objects

def _calculate_bbox_iou(bbox1: list, bbox2: list) -> float:
    """Calculate IoU between two bboxes in [x, y, width, height] format"""
    try:
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Calculate intersection
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        if xi2 <= xi1 or yi2 <= yi1:
            return 0.0
        
        intersection = (xi2 - xi1) * (yi2 - yi1)
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    except:
        return 0.0

# NOTE: get_canonical_label is now imported from app.core.taxonomy
# The old implementation is removed to avoid conflicts
# If the import fails, the fallback implementation at the top of the file will be used

def segment_objects(image: Image.Image, objects: list) -> list:
    """Generate segmentation masks for detected objects using SAM2"""
    try:
        if not objects:
            return []
            
        # Check if we have a proper SAM2 predictor or fallback string
        if models['sam2_predictor'] == "transformers_sam2":
            # Use transformers SAM2 approach
            return segment_objects_transformers(image, objects)
        
        # Use native SAM2 approach
        # Convert PIL to numpy array for SAM2
        img_array = np.array(image)
        
        # Set image for SAM2
        models['sam2_predictor'].set_image(img_array)
        
        segmented_objects = []
        for obj in objects:
            try:
                # Get bounding box center as prompt point
                # bbox format: [x, y, width, height]
                bbox = obj['bbox']
                center_x = int(bbox[0] + bbox[2] / 2)  # x + width/2
                center_y = int(bbox[1] + bbox[3] / 2)  # y + height/2
                
                # Generate mask using point prompt
                masks, scores, _ = models['sam2_predictor'].predict(
                    point_coords=np.array([[center_x, center_y]]),
                    point_labels=np.array([1]),
                    multimask_output=True
                )
                
                # Use the best mask (highest score)
                best_mask_idx = np.argmax(scores)
                mask = masks[best_mask_idx]
                
                # Calculate mask statistics with validation
                # Ensure mask is binary (0 or 1) and positive
                mask = np.clip(mask, 0, 1)  # Clamp to valid range
                mask_area = int(np.sum(mask))
                image_area = image.size[0] * image.size[1]
                
                # Validate mask area is reasonable
                if mask_area < 0:
                    logger.error(f"Invalid negative mask area: {mask_area}, setting to 0")
                    mask_area = 0
                elif mask_area > image_area:
                    logger.warning(f"Mask area {mask_area} exceeds image area {image_area}, clamping")
                    mask_area = min(mask_area, image_area)
                
                mask_coverage = mask_area / image_area if image_area > 0 else 0.0
                
                # Convert mask to base64 image
                mask_image = Image.fromarray((mask * 255).astype(np.uint8), mode='L')
                mask_buffer = io.BytesIO()
                mask_image.save(mask_buffer, format='PNG')
                mask_base64 = base64.b64encode(mask_buffer.getvalue()).decode('utf-8')

                segmented_objects.append({
                    **obj,  # Include original object data
                    "has_mask": True,
                    "mask_area": mask_area,
                    "mask_coverage": round(mask_coverage, 4),
                    "segmentation_confidence": float(scores[best_mask_idx]),
                    "mask_base64": mask_base64  # Add base64-encoded mask
                })
                
            except Exception as e:
                logger.error(f"Segmentation failed for object {obj['label']}: {e}")
                segmented_objects.append({
                    **obj,
                    "has_mask": False,
                    "mask_area": 0,
                    "mask_coverage": 0.0,
                    "segmentation_confidence": 0.0
                })
        
        return segmented_objects
        
    except Exception as e:
        logger.error(f"Object segmentation failed: {e}")
        return objects  # Return original objects without masks

def segment_objects_transformers(image: Image.Image, objects: list) -> list:
    """Generate segmentation masks using transformers SAM2 (fallback method)"""
    try:
        import torch
        
        segmented_objects = []
        for obj in objects:
            try:
                # Get bounding box for input prompts
                # bbox format: [x, y, width, height]
                bbox = obj['bbox']
                # Convert to input format for transformers SAM2 (4 levels required)
                # Format: [image level, object level, point level, point coordinates]
                center_x = int(bbox[0] + bbox[2] / 2)  # x + width/2
                center_y = int(bbox[1] + bbox[3] / 2)  # y + height/2
                input_points = [[[[center_x, center_y]]]]
                input_labels = [[[1]]]  # 1 for foreground, matching the 4-level structure
                
                # Prepare inputs
                inputs = models['sam2_processor'](
                    images=image,
                    input_points=input_points,
                    input_labels=input_labels,
                    return_tensors="pt"
                )
                
                # Move inputs to same device as model
                device = models.get('device', 'cpu')
                inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
                
                # Generate mask
                with torch.no_grad():
                    outputs = models['sam2_model'](**inputs)
                
                # Extract mask from outputs
                masks = outputs.pred_masks.squeeze().cpu().numpy()
                scores = outputs.iou_scores.squeeze().cpu().numpy()
                
                # Handle single mask case
                if masks.ndim == 2:
                    mask = masks
                    score = float(scores) if scores.ndim == 0 else float(scores[0])
                else:
                    # Multiple masks, use the best one
                    best_idx = np.argmax(scores)
                    mask = masks[best_idx]
                    score = float(scores[best_idx])
                
                # Calculate mask statistics with validation
                # Ensure mask is binary (0 or 1) and positive
                mask = np.clip(mask, 0, 1)  # Clamp to valid range
                mask_area = int(np.sum(mask))
                image_area = image.size[0] * image.size[1]
                
                # Validate mask area is reasonable
                if mask_area < 0:
                    logger.error(f"Invalid negative mask area: {mask_area}, setting to 0")
                    mask_area = 0
                elif mask_area > image_area:
                    logger.warning(f"Mask area {mask_area} exceeds image area {image_area}, clamping")
                    mask_area = min(mask_area, image_area)
                
                mask_coverage = mask_area / image_area if image_area > 0 else 0.0
                
                # Convert mask to base64 image
                mask_image = Image.fromarray((mask * 255).astype(np.uint8), mode='L')
                mask_buffer = io.BytesIO()
                mask_image.save(mask_buffer, format='PNG')
                mask_base64 = base64.b64encode(mask_buffer.getvalue()).decode('utf-8')

                segmented_objects.append({
                    **obj,  # Include original object data
                    "has_mask": True,
                    "mask_area": mask_area,
                    "mask_coverage": round(mask_coverage, 4),
                    "segmentation_confidence": score,
                    "mask_base64": mask_base64  # Add base64-encoded mask
                })
                
            except Exception as e:
                logger.error(f"Transformers segmentation failed for object {obj['label']}: {e}")
                segmented_objects.append({
                    **obj,
                    "has_mask": False,
                    "mask_area": 0,
                    "mask_coverage": 0.0,
                    "segmentation_confidence": 0.0
                })
        
        return segmented_objects
        
    except Exception as e:
        logger.error(f"Transformers object segmentation failed: {e}")
        return objects  # Return original objects without masks

def analyze_style(image: Image.Image) -> dict:
    """Analyze design style using CLIP"""
    try:
        style_prompts = [
            "contemporary interior design", "traditional interior design",
            "modern interior design", "rustic interior design", 
            "industrial interior design", "scandinavian interior design",
            "minimalist interior design", "bohemian interior design"
        ]
        
        inputs = models['clip_processor'](
            text=style_prompts,
            images=[image],  # CLIP processor expects a list of images
            return_tensors="pt", 
            padding=True
        )
        
        # Move inputs to same device as model with error handling
        device = models.get('device', 'cpu')
        try:
            inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
            logger.debug(f"Style analysis inputs moved to device {device}")
        except Exception as e:
            logger.error(f"Error moving style inputs to device {device}: {e}")
            # Fallback to CPU
            device = 'cpu'
            inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = models['clip_model'](**inputs)
            logits = outputs.logits_per_image
            probs = logits.softmax(dim=1)
        
        # Get top styles
        styles = []
        for i, style in enumerate(style_prompts):
            confidence = float(probs[0][i])
            if confidence > 0.1:  # Only confident predictions
                styles.append({
                    "style": style.replace(" interior design", ""),
                    "confidence": round(confidence, 3)
                })
        
        styles.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            "primary_style": styles[0]['style'] if styles else "contemporary",
            "style_confidence": styles[0]['confidence'] if styles else 0.5,
            "style_alternatives": styles[:3]
        }
        
    except Exception as e:
        logger.error(f"Style analysis failed: {e}")
        return {
            "primary_style": "contemporary",
            "style_confidence": 0.5,
            "style_alternatives": []
        }

def detect_object_materials(image: Image.Image, objects: list, material_taxonomy: dict = None) -> list:
    """
    Enhanced material detection using CLIP on object crops for contextual analysis.
    
    Args:
        image: Full scene PIL Image
        objects: List of detected objects with bbox and label
        material_taxonomy: Optional custom material taxonomy
        
    Returns:
        Objects enriched with materials field
    """
    if not objects:
        return []
    
    # Define comprehensive material taxonomy based on object types
    if material_taxonomy is None:
        material_taxonomy = {
            # Seating materials - Enhanced with specific textures
            "sofa": ["fabric upholstery", "leather upholstery", "velvet fabric", "linen fabric", 
                    "microfiber", "cotton blend", "corduroy", "wood frame", "metal legs", "plastic base"],
            "couch": ["fabric upholstery", "leather upholstery", "velvet fabric", "linen fabric", 
                     "microfiber", "cotton blend", "corduroy", "wood frame", "metal legs"],
            "chair": ["solid wood", "metal frame", "plastic", "fabric seat", "leather seat", "rattan", 
                     "mesh back", "wicker", "bamboo", "steel", "aluminum"],
            "armchair": ["fabric upholstery", "leather upholstery", "velvet", "wood frame", "metal legs"],
            "ottoman": ["fabric", "leather", "woven material", "wood base", "metal legs"],
            
            # Table materials - Enhanced with finishes
            "table": ["solid wood", "oak wood", "pine wood", "walnut wood", "glass top", "tempered glass",
                     "marble top", "granite surface", "metal frame", "steel legs", "laminate", 
                     "stone surface", "acrylic", "reclaimed wood", "bamboo"],
            "desk": ["wood veneer", "solid wood", "metal frame", "glass surface", "laminate top", 
                    "particle board", "steel legs", "aluminum frame"],
            "coffee_table": ["wood surface", "glass top", "metal frame", "stone surface", "marble top"],
            "dining_table": ["solid wood", "oak", "pine", "walnut", "glass top", "metal base"],
            
            # Storage materials - Enhanced with construction details
            "cabinet": ["solid wood", "plywood", "metal", "laminate finish", "glass doors", 
                       "particle board", "MDF", "wood veneer", "steel frame"],
            "shelf": ["wood", "metal brackets", "glass shelves", "wire mesh", "plastic", "steel"],
            "bookshelf": ["solid wood", "wood veneer", "metal frame", "particle board", "laminate"],
            "dresser": ["solid wood", "wood veneer", "laminate finish", "metal handles", "wood handles"],
            "wardrobe": ["wood construction", "metal frame", "fabric doors", "mirror doors"],
            
            # Bedroom materials - Enhanced
            "bed": ["wood frame", "metal frame", "upholstered headboard", "fabric headboard", 
                   "leather headboard", "solid wood", "steel frame", "iron frame"],
            "mattress": ["memory foam", "latex foam", "spring coils", "fabric cover", "cotton cover"],
            "nightstand": ["solid wood", "wood veneer", "metal", "glass top", "laminate"],
            
            # Lighting materials - Enhanced
            "lamp": ["metal base", "ceramic base", "wood base", "glass shade", "fabric shade", 
                    "paper shade", "plastic shade", "steel construction", "brass finish"],
            "ceiling_light": ["metal fixture", "glass shade", "fabric shade", "LED panel", "chrome finish"],
            "floor_lamp": ["metal pole", "wood base", "fabric shade", "paper shade", "steel base"],
            
            # Textiles and soft goods
            "pillow": ["cotton fabric", "linen", "velvet", "silk", "polyester", "down filling", "foam filling"],
            "curtains": ["cotton fabric", "linen", "polyester", "silk", "sheer fabric", "blackout fabric"],
            "rug": ["wool", "cotton", "synthetic fibers", "jute", "sisal", "silk", "bamboo"],
            "carpet": ["wool pile", "nylon", "polyester", "natural fibers"],
            
            # Decorative items
            "mirror": ["glass surface", "metal frame", "wood frame", "plastic frame", "silver backing"],
            "plant": ["natural foliage", "ceramic pot", "plastic pot", "terra cotta", "metal planter"],
            "vase": ["ceramic", "glass", "metal", "plastic", "stone", "clay"],
            "artwork": ["canvas", "paper", "metal print", "wood frame", "plastic frame"],
            
            # Kitchen and bathroom
            "sink": ["stainless steel", "ceramic", "granite composite", "marble", "copper"],
            "faucet": ["chrome finish", "stainless steel", "brass finish", "nickel finish"],
            "toilet": ["ceramic", "porcelain"],
            "bathtub": ["acrylic", "fiberglass", "cast iron", "stone"],
            
            # Default fallback for unknown objects
            "default": ["wood", "metal", "plastic", "glass", "fabric", "ceramic", "stone"]
        }
    
    try:
        enhanced_objects = []
        
        for obj in objects:
            enhanced_obj = obj.copy()
            
            try:
                # Get object label and bbox
                label = obj.get("label", "unknown")
                bbox = obj.get("bbox", [])
                
                # Skip if no valid bbox
                if not bbox or len(bbox) < 4:
                    enhanced_obj["materials"] = []
                    enhanced_objects.append(enhanced_obj)
                    continue
                
                # Extract object crop
                x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]
                
                # Validate bbox dimensions
                if w <= 0 or h <= 0:
                    enhanced_obj["materials"] = []
                    enhanced_objects.append(enhanced_obj)
                    continue
                
                # Crop object from image
                object_crop = image.crop((x, y, x + w, y + h))
                
                # Get material candidates based on object type
                material_candidates = material_taxonomy.get(label, material_taxonomy.get("default", []))
                
                # Prepare enhanced material prompts for CLIP with context
                material_prompts = []
                for mat in material_candidates:
                    # Enhanced prompting with object context for better accuracy
                    if "fabric" in mat or "upholstery" in mat:
                        material_prompts.append(f"a photo of {label} with {mat}")
                        material_prompts.append(f"furniture made from {mat}")
                    elif "wood" in mat or "metal" in mat or "glass" in mat:
                        material_prompts.append(f"a photo of {label} made from {mat}")
                        material_prompts.append(f"{mat} {label}")
                    else:
                        material_prompts.append(f"a photo of {mat} {label}")
                        material_prompts.append(f"{label} with {mat}")
                
                # Deduplicate prompts while preserving order
                material_prompts = list(dict.fromkeys(material_prompts))
                
                if not material_prompts:
                    enhanced_obj["materials"] = []
                    enhanced_objects.append(enhanced_obj)
                    continue
                
                # Run CLIP on object crop with material prompts
                inputs = models['clip_processor'](
                    text=material_prompts,
                    images=[object_crop],  # CLIP processor expects a list of images
                    return_tensors="pt",
                    padding=True
                )
                
                # Move inputs to same device as model with error handling
                device = models.get('device', 'cpu')
                try:
                    inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
                except Exception as e:
                    logger.error(f"Error moving material inputs to device {device}: {e}")
                    # Fallback to CPU
                    device = 'cpu'
                    inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = models['clip_model'](**inputs)
                    logits = outputs.logits_per_image
                    probs = logits.softmax(dim=1)
                
                # Adaptive confidence thresholds based on object type
                confidence_thresholds = {
                    "sofa": 0.20,      # Higher threshold for complex objects
                    "chair": 0.20,
                    "table": 0.18,
                    "bed": 0.20,
                    "cabinet": 0.18,
                    "lamp": 0.15,
                    "plant": 0.25,     # Higher for organic materials
                    "mirror": 0.30,    # Very high for simple materials
                    "rug": 0.22,
                    "curtains": 0.22,
                    "pillow": 0.20
                }
                
                threshold = confidence_thresholds.get(label, 0.15)
                
                # Extract materials above threshold
                materials = []
                for i, material in enumerate(material_candidates):
                    confidence = float(probs[0][i])
                    if confidence > threshold:
                        materials.append({
                            "material": material,
                            "confidence": round(confidence, 3)
                        })
                
                # Sort by confidence
                materials.sort(key=lambda x: x['confidence'], reverse=True)
                
                # Limit to top 3 materials
                enhanced_obj["materials"] = materials[:3]
                
                # Add material summary to object
                if materials:
                    top_material = materials[0]["material"]
                    enhanced_obj["primary_material"] = top_material
                    enhanced_obj["material_confidence"] = materials[0]["confidence"]
                else:
                    enhanced_obj["materials"] = []
                    enhanced_obj["primary_material"] = "unknown"
                    enhanced_obj["material_confidence"] = 0.0
                
                logger.debug(f"Object {label}: detected {len(materials)} materials")
                
            except Exception as e:
                logger.error(f"Material detection failed for object {obj.get('label', 'unknown')}: {e}")
                enhanced_obj["materials"] = []
                enhanced_obj["primary_material"] = "unknown"
                enhanced_obj["material_confidence"] = 0.0
            
            enhanced_objects.append(enhanced_obj)
        
        # Log material detection statistics
        total_objects = len(enhanced_objects)
        with_materials = sum(1 for obj in enhanced_objects if obj.get("materials"))
        logger.info(f"Material detection: {with_materials}/{total_objects} objects with materials detected")
        
        return enhanced_objects
        
    except Exception as e:
        logger.error(f"Enhanced material detection failed: {e}")
        return objects  # Return original objects on failure

def analyze_materials(image: Image.Image, objects: list) -> dict:
    """Legacy material analysis function for backwards compatibility"""
    try:
        # Use new enhanced material detection
        enhanced_objects = detect_object_materials(image, objects)
        
        # Aggregate materials from all objects
        all_materials = {}
        for obj in enhanced_objects:
            for mat_info in obj.get("materials", []):
                material = mat_info["material"]
                confidence = mat_info["confidence"]
                if material in all_materials:
                    all_materials[material] = max(all_materials[material], confidence)
                else:
                    all_materials[material] = confidence
        
        # Convert to list format
        materials = [
            {"material": mat, "confidence": round(conf, 3)}
            for mat, conf in all_materials.items()
        ]
        materials.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            "dominant_materials": materials[:3],
            "all_materials": materials
        }
        
    except Exception as e:
        logger.error(f"Material analysis failed: {e}")
        return {
            "dominant_materials": [{"material": "unknown", "confidence": 0.0}],
            "all_materials": []
        }

def extract_color_palette(image: Image.Image) -> dict:
    """Extract dominant colors from the image using enhanced algorithm"""
    try:
        # Try to use enhanced color extraction if available
        try:
            from app.services.color_extraction import extract_color_palette_advanced
            result = extract_color_palette_advanced(
                image, 
                n_colors=5, 
                sample_fraction=0.1,
                seed=42  # For reproducibility
            )
            logger.info(f"Color extraction using {result.get('extraction_method', 'unknown')} method")
            return result
        except ImportError:
            logger.debug("Enhanced color extraction not available, using fallback")
        
        # Fallback to simple method if enhanced not available
        # Resize image for faster processing
        img_resized = image.resize((150, 150))
        img_array = np.array(img_resized)
        
        # Reshape to list of pixels
        pixels = img_resized.getdata()
        
        # Simple color clustering (get most common colors)
        from collections import Counter
        color_counts = Counter(pixels)
        
        # Get top 5 most common colors
        dominant_colors = []
        for color, count in color_counts.most_common(5):
            if isinstance(color, tuple) and len(color) == 3:
                dominant_colors.append({
                    "rgb": list(color),
                    "hex": "#{:02x}{:02x}{:02x}".format(*color),
                    "frequency": round(count / len(pixels), 3)
                })
        
        return {
            "dominant_colors": dominant_colors,
            "palette_size": len(dominant_colors),
            "extraction_method": "pixel_count"
        }
        
    except Exception as e:
        logger.error(f"Color palette extraction failed: {e}")
        return {
            "dominant_colors": [],
            "palette_size": 0,
            "extraction_method": "error"
        }

def estimate_depth(image: Image.Image) -> dict:
    """Generate depth map using depth estimation model"""
    try:
        # Run depth estimation
        depth_result = models['depth'](image)
        
        # Extract depth information
        depth_map = depth_result['depth']
        if hasattr(depth_map, 'numpy'):
            depth_array = depth_map.numpy()
        else:
            depth_array = np.array(depth_map)
        
        # Create depth visualization
        # Normalize depth array to 0-255 for visualization
        depth_normalized = ((depth_array - depth_array.min()) / (depth_array.max() - depth_array.min()) * 255).astype(np.uint8)
        
        # Convert to PIL Image and then to base64
        depth_image = Image.fromarray(depth_normalized, mode='L')
        depth_buffer = io.BytesIO()
        depth_image.save(depth_buffer, format='PNG')
        depth_base64 = base64.b64encode(depth_buffer.getvalue()).decode('utf-8')

        return {
            "depth_available": True,
            "depth_stats": {
                "min_depth": float(depth_array.min()),
                "max_depth": float(depth_array.max()), 
                "mean_depth": float(depth_array.mean()),
                "depth_range": float(depth_array.max() - depth_array.min())
            },
            "depth_base64": depth_base64  # Add base64-encoded depth map
        }
        
    except Exception as e:
        logger.error(f"Depth estimation failed: {e}")
        return {
            "depth_available": False,
            "depth_stats": {
                "min_depth": 0.0,
                "max_depth": 10.0,
                "mean_depth": 3.0,
                "depth_range": 10.0
            }
        }

def enhance_objects_with_details(image: Image.Image, objects: list, depth_map: Image.Image = None) -> list:
    """
    Generate object thumbnails, descriptions, and depth crops for detected objects.
    
    Args:
        image: Original scene image
        objects: List of detected objects with bounding boxes
        depth_map: Optional depth map for generating object depth crops
        
    Returns:
        Enhanced objects with thumb_base64, description, and depth_base64 fields
    """
    try:
        enhanced_objects = []
        
        for obj in objects:
            enhanced_obj = obj.copy()
            
            try:
                # Get bounding box coordinates - format: [x, y, width, height]
                bbox = obj.get("bbox", [])
                if isinstance(bbox, list) and len(bbox) >= 4:
                    # Standard format: [x, y, width, height]
                    x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]
                    x = int(x)
                    y = int(y) 
                    w = int(w)
                    h = int(h)
                elif isinstance(bbox, dict):
                    # Dictionary format: {x, y, width, height}
                    x = int(bbox.get("x", 0))
                    y = int(bbox.get("y", 0))
                    w = int(bbox.get("width", 0))
                    h = int(bbox.get("height", 0))
                else:
                    logger.warning(f"Unsupported bbox format for object {obj.get('label', 'unknown')}: {bbox}")
                    enhanced_objects.append(enhanced_obj)
                    continue
                
                # Skip if bbox is invalid
                if w <= 0 or h <= 0:
                    logger.warning(f"Invalid bbox for object {obj.get('label', 'unknown')}: {bbox}")
                    enhanced_objects.append(enhanced_obj)
                    continue
                
                # Crop object from image for thumbnail generation
                object_crop = image.crop((x, y, x + w, y + h))
                
                # Generate object thumbnail (128x128 max)
                thumbnail = object_crop.copy()
                thumbnail.thumbnail((128, 128), Image.Resampling.LANCZOS)
                
                # Convert thumbnail to base64
                thumb_buffer = io.BytesIO()
                thumbnail.save(thumb_buffer, format='JPEG', quality=85, optimize=True)
                thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode('utf-8')
                enhanced_obj["thumb_base64"] = thumb_base64
                
                # Generate object description using CLIP
                label = obj.get("label", "object")
                material = obj.get("material", "")
                confidence = obj.get("confidence", 0.0)
                
                # Create descriptive text based on available information
                if material and confidence > 0.7:
                    description = f"{material} {label} with {confidence*100:.0f}% confidence"
                elif confidence > 0.5:
                    description = f"{label} detected with {confidence*100:.0f}% confidence"
                else:
                    description = f"{label} object"
                
                # Add area information if available
                if "area" in obj:
                    area_desc = f", area: {obj['area']:.0f} pixels"
                    description += area_desc
                
                enhanced_obj["description"] = description
                
                # Generate depth crop if depth map is available
                if depth_map is not None:
                    try:
                        # Crop depth map using same bbox
                        depth_crop = depth_map.crop((x, y, x + w, y + h))
                        
                        # Convert depth crop to base64
                        depth_buffer = io.BytesIO()
                        depth_crop.save(depth_buffer, format='PNG')
                        depth_base64 = base64.b64encode(depth_buffer.getvalue()).decode('utf-8')
                        
                        enhanced_obj["depth_base64"] = depth_base64
                        enhanced_obj["has_depth_crop"] = True
                        
                        # Calculate depth statistics for the object
                        depth_array = np.array(depth_crop)
                        if depth_array.size > 0:
                            enhanced_obj["depth_stats"] = {
                                "min_depth": float(np.min(depth_array)),
                                "max_depth": float(np.max(depth_array)),
                                "mean_depth": float(np.mean(depth_array)),
                                "depth_range": float(np.max(depth_array) - np.min(depth_array))
                            }
                        
                    except Exception as e:
                        logger.warning(f"Failed to generate depth crop for {label}: {e}")
                        enhanced_obj["has_depth_crop"] = False
                else:
                    enhanced_obj["has_depth_crop"] = False
                
                logger.debug(f"Enhanced object {label}: thumb={len(thumb_base64)} chars, desc='{description[:50]}...'")
                
            except Exception as e:
                logger.error(f"Failed to enhance object {obj.get('label', 'unknown')}: {e}")
                # Add empty enhancement fields on error
                enhanced_obj["description"] = obj.get("label", "object")
                enhanced_obj["has_depth_crop"] = False
            
            enhanced_objects.append(enhanced_obj)
        
        logger.info(f"Enhanced {len(enhanced_objects)} objects with thumbnails and descriptions")
        return enhanced_objects
        
    except Exception as e:
        logger.error(f"Object enhancement failed: {e}")
        return objects  # Return original objects on failure

def process_scene_complete(image_data_b64: str, scene_id: str, options: dict = None) -> dict:
    """Complete scene processing pipeline"""
    start_time = time.time()
    
    try:
        # Decode and load image with validation
        logger.debug(f"Decoding image for scene {scene_id}")
        image_bytes = base64.b64decode(image_data_b64)
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # Validate image
        if image.size[0] <= 0 or image.size[1] <= 0:
            raise ValueError(f"Invalid image dimensions: {image.size}")
        
        logger.info(f"Processing scene {scene_id}, image size: {image.size} ({image.mode})")
        
        # Generate thumbnail (256x256 max, maintaining aspect ratio)
        thumbnail = image.copy()
        thumbnail.thumbnail((256, 256), Image.Resampling.LANCZOS)
        
        # Convert thumbnail to base64
        thumb_buffer = io.BytesIO()
        thumbnail.save(thumb_buffer, format='JPEG', quality=85, optimize=True)
        thumbnail_base64 = base64.b64encode(thumb_buffer.getvalue()).decode('utf-8')
        
        results = {
            "scene_id": scene_id,
            "processing_started": time.time(),
            "image_size": image.size,
            "thumbnail_base64": thumbnail_base64  # Add thumbnail
        }
        
        # Run AI analysis pipeline
        try:
            logger.info("Running scene classification...")
            scene_analysis = classify_scene(image)
            results["scene_analysis"] = scene_analysis
        except Exception as e:
            logger.error(f"Scene classification failed: {e}")
            raise e
        
        try:
            logger.info("Running object detection...")
            objects = detect_objects(image)
            results["objects_detected"] = len(objects)
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            raise e
        
        try:
            logger.info("Running object segmentation...")
            segmented_objects = segment_objects(image, objects)
        except Exception as e:
            logger.error(f"Object segmentation failed: {e}")
            raise e
        
        try:
            logger.info("Running style analysis...")
            style_analysis = analyze_style(image)
            results["style_analysis"] = style_analysis
        except Exception as e:
            logger.error(f"Style analysis failed: {e}")
            raise e
        
        try:
            logger.info("Running depth estimation...")
            depth_analysis = estimate_depth(image)
            results["depth_analysis"] = depth_analysis
        except Exception as e:
            logger.error(f"Depth estimation failed: {e}")
            raise e
        
        # Extract depth map for object enhancement
        depth_map = None
        if depth_analysis.get("depth_available"):
            try:
                depth_base64 = depth_analysis.get("depth_base64", "")
                if depth_base64:
                    depth_data = base64.b64decode(depth_base64)
                    depth_map = Image.open(io.BytesIO(depth_data))
            except Exception as e:
                logger.warning(f"Failed to load depth map for object enhancement: {e}")
        
        logger.info("Running material analysis...")
        material_analysis = analyze_materials(image, segmented_objects)
        results["material_analysis"] = material_analysis
        
        logger.info("Generating object thumbnails, descriptions, and depth crops...")
        enhanced_objects = enhance_objects_with_details(image, segmented_objects, depth_map)
        results["objects"] = enhanced_objects  # Use enhanced objects as primary output
        
        logger.info("Extracting color palette...")
        color_palette = extract_color_palette(image)
        results["color_palette"] = color_palette
        
        # Processing complete
        processing_time = time.time() - start_time
        results["processing_time"] = round(processing_time, 2)
        results["processing_completed"] = time.time()
        
        logger.info(f"✅ Scene {scene_id} processed in {processing_time:.2f}s")
        logger.info(f"   Scene: {scene_analysis['scene_type']} ({scene_analysis['confidence']:.2f})")
        logger.info(f"   Objects: {len(segmented_objects)}")
        logger.info(f"   Style: {style_analysis['primary_style']} ({style_analysis['style_confidence']:.2f})")
        
        return {
            "status": "success",
            "result": results
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        processing_time = time.time() - start_time
        logger.error(f"❌ Scene processing failed after {processing_time:.2f}s: {e}")
        logger.error(f"Full traceback: {error_trace}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": error_trace,
            "processing_time": round(processing_time, 2)
        }

def batch_process_scenes(images: list, batch_size: int = 4, options: dict = None) -> list:
    """
    Process multiple scenes in batches for improved GPU utilization.
    
    Args:
        images: List of tuples [(scene_id, base64_image), ...]
        batch_size: Max images per GPU batch (1-8)
        options: Processing options dict
        
    Returns:
        List of results in same order as input
    """
    if options is None:
        options = {}
    
    # Validate inputs
    batch_size = max(1, min(8, batch_size))
    if not images:
        return []
    
    logger.info(f"📦 Batch processing {len(images)} scenes with batch_size={batch_size}")
    start_time = time.time()
    
    # Set seed for determinism
    torch.manual_seed(42)
    np.random.seed(42)
    
    results = []
    
    # Process in batches
    for i in range(0, len(images), batch_size):
        batch = images[i:i+batch_size]
        batch_start = time.time()
        
        try:
            # Decode all images in batch
            pil_images = []
            scene_ids = []
            
            for scene_id, image_b64 in batch:
                try:
                    image_bytes = base64.b64decode(image_b64)
                    pil_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
                    pil_images.append(pil_image)
                    scene_ids.append(scene_id)
                except Exception as e:
                    logger.error(f"Failed to decode image for scene {scene_id}: {e}")
                    results.append({
                        "scene_id": scene_id,
                        "status": "error",
                        "error": f"Image decode failed: {str(e)}"
                    })
            
            if not pil_images:
                continue
            
            # Batch inference with automatic batch size reduction on OOM
            current_batch_size = len(pil_images)
            while current_batch_size > 0:
                try:
                    batch_results = _process_batch_gpu(pil_images[:current_batch_size], 
                                                       scene_ids[:current_batch_size], 
                                                       options)
                    results.extend(batch_results)
                    
                    # Process remaining if batch was reduced
                    if current_batch_size < len(pil_images):
                        remaining_results = _process_batch_gpu(pil_images[current_batch_size:],
                                                              scene_ids[current_batch_size:],
                                                              options)
                        results.extend(remaining_results)
                    break
                    
                except torch.cuda.OutOfMemoryError:
                    logger.warning(f"GPU OOM with batch_size={current_batch_size}, reducing...")
                    torch.cuda.empty_cache()
                    current_batch_size = current_batch_size // 2
                    if current_batch_size == 0:
                        # Fall back to single image processing
                        for img, sid in zip(pil_images, scene_ids):
                            result = _process_single_scene(img, sid, options)
                            results.append(result)
                        break
            
            batch_time = time.time() - batch_start
            logger.info(f"Batch {i//batch_size + 1} processed in {batch_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # Process failed batch individually
            for scene_id, image_b64 in batch:
                results.append({
                    "scene_id": scene_id,
                    "status": "error", 
                    "error": f"Batch processing failed: {str(e)}"
                })
    
    total_time = time.time() - start_time
    avg_time = total_time / len(images) if images else 0
    logger.info(f"✅ Batch processing complete: {len(images)} scenes in {total_time:.2f}s (avg {avg_time:.2f}s/image)")
    
    return results

def _process_batch_gpu(pil_images: list, scene_ids: list, options: dict) -> list:
    """Process a batch of images on GPU with batched inference."""
    results = []
    
    # Batch CLIP inference for scene classification and styles
    scene_classifications = _batch_classify_scenes(pil_images)
    style_analyses = _batch_analyze_styles(pil_images)
    
    # Batch YOLO inference
    all_objects = _batch_detect_objects(pil_images)
    
    # Process each image's results
    for img, scene_id, scene_class, style, objects in zip(
        pil_images, scene_ids, scene_classifications, style_analyses, all_objects
    ):
        # Individual processing for segmentation and enhancement
        segmented = segment_objects(img, objects)
        materials = detect_object_materials(img, segmented)
        
        # Get depth map for object enhancement
        depth = estimate_depth(img)
        depth_map = None
        if depth.get("depth_available"):
            try:
                depth_base64 = depth.get("depth_base64", "")
                if depth_base64:
                    depth_data = base64.b64decode(depth_base64)
                    depth_map = Image.open(io.BytesIO(depth_data))
            except Exception as e:
                logger.warning(f"Failed to load depth map for batch processing: {e}")
        
        enhanced = enhance_objects_with_details(img, materials, depth_map)
        colors = extract_color_palette(img)
        
        # Generate thumbnail
        thumbnail = img.copy()
        thumbnail.thumbnail((256, 256), Image.Resampling.LANCZOS)
        thumb_buffer = io.BytesIO()
        thumbnail.save(thumb_buffer, format='JPEG', quality=85)
        thumbnail_b64 = base64.b64encode(thumb_buffer.getvalue()).decode('utf-8')
        
        results.append({
            "scene_id": scene_id,
            "status": "success",
            "scene_analysis": scene_class,
            "style_analysis": style,
            "objects": enhanced,
            "objects_detected": len(enhanced),
            "material_analysis": {"dominant_materials": [], "all_materials": []},
            "color_palette": colors,
            "depth_analysis": depth,
            "thumbnail_base64": thumbnail_b64,
            "image_size": img.size
        })
    
    return results

def _batch_classify_scenes(images: list) -> list:
    """Batch scene classification using CLIP."""
    scene_types = [
        "a bedroom interior", "a living room interior", "a kitchen interior",
        "a bathroom interior", "a dining room interior", "an office interior",
        "a hallway interior", "an outdoor patio", "a garage interior"
    ]
    
    # Batch process all images at once
    inputs = models['clip_processor'](
        text=scene_types,
        images=images,
        return_tensors="pt",
        padding=True
    )
    
    # Move inputs to same device as model
    device = models.get('device', 'cpu')
    inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = models['clip_model'](**inputs)
        logits = outputs.logits_per_image
        probs = logits.softmax(dim=1)
    
    results = []
    for i in range(len(images)):
        best_idx = probs[i].argmax().item()
        confidence = probs[i][best_idx].item()
        scene_type = scene_types[best_idx].replace("a ", "").replace("an ", "").replace(" interior", "")
        
        top_indices = probs[i].argsort(descending=True)[:3]
        alternatives = [
            {
                "type": scene_types[idx].replace("a ", "").replace("an ", "").replace(" interior", ""),
                "confidence": float(probs[i][idx])
            }
            for idx in top_indices
        ]
        
        results.append({
            "scene_type": scene_type,
            "confidence": float(confidence),
            "alternatives": alternatives
        })
    
    return results

def _batch_analyze_styles(images: list) -> list:
    """Batch style analysis using CLIP."""
    style_prompts = [
        "contemporary interior design", "traditional interior design",
        "modern interior design", "rustic interior design",
        "industrial interior design", "scandinavian interior design",
        "minimalist interior design", "bohemian interior design"
    ]
    
    inputs = models['clip_processor'](
        text=style_prompts,
        images=images,
        return_tensors="pt",
        padding=True
    )
    
    # Move inputs to same device as model
    device = models.get('device', 'cpu')
    inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = models['clip_model'](**inputs)
        logits = outputs.logits_per_image
        probs = logits.softmax(dim=1)
    
    results = []
    for i in range(len(images)):
        styles = []
        for j, style in enumerate(style_prompts):
            confidence = float(probs[i][j])
            if confidence > 0.1:
                styles.append({
                    "style": style.replace(" interior design", ""),
                    "confidence": round(confidence, 3)
                })
        
        styles.sort(key=lambda x: x['confidence'], reverse=True)
        
        results.append({
            "primary_style": styles[0]['style'] if styles else "contemporary",
            "style_confidence": styles[0]['confidence'] if styles else 0.5,
            "style_alternatives": styles[:3]
        })
    
    return results

def _batch_detect_objects(images: list) -> list:
    """Enhanced batch object detection using YOLO."""
    # Convert PIL images to numpy arrays
    img_arrays = [np.array(img) for img in images]
    
    # Run enhanced batch inference with optimized parameters
    batch_results = models['yolo'](
        img_arrays, 
        conf=0.15,          # Lower threshold to catch more objects
        iou=0.45,           # Better NMS threshold
        agnostic_nms=True,  # Class-agnostic NMS
        max_det=50,         # Allow more detections
        verbose=False
    )
    
    all_objects = []
    for result, img in zip(batch_results, images):
        objects = []
        if result.boxes is not None:
            for box in result.boxes:
                coords = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = float(coords[0]), float(coords[1]), float(coords[2]), float(coords[3])
                
                # Validate coordinates
                if x2 < x1:
                    x1, x2 = x2, x1
                if y2 < y1:
                    y1, y2 = y2, y1
                
                if (x2 - x1) < 1 or (y2 - y1) < 1:
                    continue
                
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                label = models['yolo'].names[cls]
                
                # Enhanced filtering with adaptive confidence thresholds
                canonical_label = get_canonical_label(label.lower())
                is_known_furniture = canonical_label in get_yolo_whitelist()
                
                # Adaptive confidence based on object type and knowledge
                min_conf_threshold = 0.20 if is_known_furniture else 0.35
                
                if is_furniture_item(label, conf, min_conf=min_conf_threshold):
                    objects.append({
                        "label": canonical_label,
                        "confidence": round(conf, 3),
                        "bbox": [int(x1), int(y1), int(x2 - x1), int(y2 - y1)],
                        "bbox_format": "xywh",
                        "area": int((x2 - x1) * (y2 - y1))
                    })
        
        # Enhanced post-processing
        objects = [obj for obj in objects if obj['area'] >= 100]
        objects = _filter_overlapping_objects(objects)
        objects.sort(key=lambda x: (x['confidence'], x['area']), reverse=True)
        all_objects.append(objects[:30])
    
    return all_objects

def _process_single_scene(image: Image.Image, scene_id: str, options: dict) -> dict:
    """Fallback to single scene processing."""
    try:
        # Use existing single-image functions
        scene_analysis = classify_scene(image)
        objects = detect_objects(image)
        segmented = segment_objects(image, objects)
        materials = detect_object_materials(image, segmented)
        
        # Get depth map for object enhancement
        depth = estimate_depth(image)
        depth_map = None
        if depth.get("depth_available"):
            try:
                depth_base64 = depth.get("depth_base64", "")
                if depth_base64:
                    depth_data = base64.b64decode(depth_base64)
                    depth_map = Image.open(io.BytesIO(depth_data))
            except Exception as e:
                logger.warning(f"Failed to load depth map for single scene processing: {e}")
        
        enhanced = enhance_objects_with_details(image, materials, depth_map)
        style = analyze_style(image)
        colors = extract_color_palette(image)
        
        # Generate thumbnail
        thumbnail = image.copy()
        thumbnail.thumbnail((256, 256), Image.Resampling.LANCZOS)
        thumb_buffer = io.BytesIO()
        thumbnail.save(thumb_buffer, format='JPEG', quality=85)
        thumbnail_b64 = base64.b64encode(thumb_buffer.getvalue()).decode('utf-8')
        
        return {
            "scene_id": scene_id,
            "status": "success",
            "scene_analysis": scene_analysis,
            "style_analysis": style,
            "objects": enhanced,
            "objects_detected": len(enhanced),
            "color_palette": colors,
            "depth_analysis": depth,
            "thumbnail_base64": thumbnail_b64,
            "image_size": image.size
        }
    except Exception as e:
        logger.error(f"Single scene processing failed for {scene_id}: {e}")
        return {
            "scene_id": scene_id,
            "status": "error",
            "error": str(e)
        }

def check_gpu_utilization():
    """Check GPU utilization and memory usage"""
    try:
        import torch
        if not torch.cuda.is_available():
            return {
                "gpu_available": False,
                "message": "No GPU available"
            }
        
        device_count = torch.cuda.device_count()
        gpu_info = []
        
        for i in range(device_count):
            device_props = torch.cuda.get_device_properties(i)
            memory_used = torch.cuda.memory_allocated(i)
            memory_total = device_props.total_memory
            memory_percent = (memory_used / memory_total) * 100
            
            gpu_info.append({
                "device_id": i,
                "name": device_props.name,
                "memory_used_mb": memory_used // (1024**2),
                "memory_total_mb": memory_total // (1024**2),
                "memory_usage_percent": round(memory_percent, 2),
                "is_current_device": i == torch.cuda.current_device()
            })
        
        return {
            "gpu_available": True,
            "device_count": device_count,
            "current_device": torch.cuda.current_device(),
            "devices": gpu_info
        }
    except Exception as e:
        return {
            "gpu_available": False,
            "error": str(e)
        }

def handler(event):
    """Main RunPod serverless handler with batch processing support"""
    try:
        logger.info(f"🔄 Handler invoked: {event.get('id', 'unknown')}")
        
        # Load models on first request
        if not models:
            logger.info("Loading models on cold start...")
            if not load_models():
                return {
                    "status": "error",
                    "error": "Failed to load AI models"
                }
        
        # Extract input data
        input_data = event.get("input", {})
        logger.info(f"Input data keys: {list(input_data.keys())}")
        
        # GPU diagnostics check
        if input_data.get("gpu_check"):
            gpu_status = check_gpu_utilization()
            return {
                "status": "success",
                "gpu_diagnostics": gpu_status,
                "models_device": models.get('device', 'unknown'),
                "models_loaded": list(models.keys())
            }
        
        # Health check
        if input_data.get("health_check"):
            gpu_status = check_gpu_utilization()
            return {
                "status": "success",
                "message": "Modomo AI pipeline is healthy",
                "models_loaded": len(models) > 0,
                "available_models": list(models.keys()),
                "device": models.get('device', 'unknown'),
                "gpu_status": gpu_status
            }
        
        # Check for batch processing
        batch_images = input_data.get("batch_images")
        if batch_images:
            # Batch processing mode
            batch_size = input_data.get("batch_size", 4)
            options = input_data.get("options", {})
            
            results = batch_process_scenes(batch_images, batch_size, options)
            return {
                "status": "success",
                "batch_results": results,
                "batch_size": len(results)
            }
        
        # Single image processing (backwards compatible)
        image_data = input_data.get("image")
        scene_id = input_data.get("scene_id", f"scene_{int(time.time())}")
        options = input_data.get("options", {})
        
        if not image_data:
            return {
                "status": "error",
                "error": "No image data provided. Send base64 encoded image in 'image' field or batch in 'batch_images'."
            }
        
        # Process the scene
        result = process_scene_complete(image_data, scene_id, options)
        return result
        
    except Exception as e:
        logger.error(f"❌ Handler error: {e}")
        return {
            "status": "error",
            "error": f"Handler failed: {str(e)}"
        }

# Start RunPod serverless
if __name__ == "__main__":
    logger.info("🚀 Starting Modomo AI Pipeline on RunPod")
    runpod.serverless.start({"handler": handler})
