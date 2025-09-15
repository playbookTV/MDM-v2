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
from PIL import Image
import torch
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        # Load CLIP for scene classification and style analysis
        logger.info("Loading CLIP model...")
        from transformers import CLIPProcessor, CLIPModel
        models['clip_model'] = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        models['clip_processor'] = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        logger.info("✅ CLIP loaded")
        
        # Load YOLO for object detection  
        logger.info("Loading YOLO model...")
        from ultralytics import YOLO
        models['yolo'] = YOLO('yolov8n.pt')  # Nano version for speed
        logger.info("✅ YOLO loaded")
        
        # Load SAM2 for segmentation
        logger.info("Loading SAM2 model...")
        try:
            from sam2.build_sam import build_sam2
            from sam2.sam2_image_predictor import SAM2ImagePredictor

            # Download and use SAM2 properly
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading SAM2 on device: {device}")

            # Use the correct SAM2 model loading
            sam2_checkpoint = "facebook/sam2-hiera-large"
            sam2_model_cfg = "sam2_hiera_l.yaml"

            # Build the model properly
            sam2_model = build_sam2(sam2_model_cfg, sam2_checkpoint, device=device)
            models['sam2_predictor'] = SAM2ImagePredictor(sam2_model)

            logger.info("✅ SAM2 loaded successfully")

        except Exception as e:
            logger.error(f"SAM2 loading failed: {e}")
            # Try alternative loading method
            try:
                logger.info("Trying alternative SAM2 loading method...")
                from transformers import Sam2Model, Sam2Processor

                models['sam2_model'] = Sam2Model.from_pretrained("facebook/sam2-hiera-large")
                models['sam2_processor'] = Sam2Processor.from_pretrained("facebook/sam2-hiera-large")
                models['sam2_predictor'] = "transformers_sam2"  # Flag for different method

                logger.info("✅ SAM2 loaded via transformers")

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
        logger.info("✅ Depth estimation loaded")
        
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
            images=image, 
            return_tensors="pt", 
            padding=True
        )
        
        with torch.no_grad():
            outputs = models['clip_model'](**inputs)
            logits = outputs.logits_per_image
            probs = logits.softmax(dim=1)
        
        # Get top prediction
        best_idx = probs.argmax().item()
        confidence = probs[0][best_idx].item()
        scene_type = scene_types[best_idx].replace("a ", "").replace(" interior", "")
        
        # Get top 3 alternatives
        top_indices = probs[0].argsort(descending=True)[:3]
        alternatives = []
        for idx in top_indices:
            alternatives.append({
                "type": scene_types[idx].replace("a ", "").replace(" interior", ""),
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
    """Detect objects using YOLO"""
    try:
        # Convert PIL to numpy for YOLO
        img_array = np.array(image)
        
        # Run YOLO inference
        results = models['yolo'](img_array, conf=0.25, verbose=False)
        
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
                        logger.warning(f"Invalid bbox dimensions for {models['yolo'].names[int(box.cls[0])]}: ({x1:.1f},{y1:.1f},{x2:.1f},{y2:.1f})")
                        continue
                    
                    # Debug log valid detections
                    logger.debug(f"Valid detection: {models['yolo'].names[int(box.cls[0])]} at ({x1:.1f},{y1:.1f},{x2:.1f},{y2:.1f})")
                    
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = models['yolo'].names[cls]
                    
                    # Comprehensive furniture/interior objects taxonomy
                    # Based on MODOMO_TAXONOMY - flattened for YOLO detection
                    furniture_objects = {
                        # Seating
                        'chair', 'couch', 'sofa', 'sectional', 'armchair', 'dining_chair', 'stool', 
                        'bench', 'loveseat', 'recliner', 'chaise_lounge', 'bar_stool', 'office_chair',
                        
                        # Tables  
                        'table', 'dining_table', 'coffee_table', 'side_table', 'console_table', 
                        'desk', 'nightstand', 'end_table',
                        
                        # Storage
                        'bookshelf', 'cabinet', 'dresser', 'wardrobe', 'tv_stand', 'shelf',
                        
                        # Bedroom
                        'bed', 'bed_frame', 'mattress', 'headboard',
                        
                        # Kitchen & Appliances
                        'refrigerator', 'stove', 'oven', 'microwave', 'dishwasher', 'sink',
                        'toaster', 'coffee_maker',
                        
                        # Bathroom
                        'toilet', 'bathtub', 'shower',
                        
                        # Lighting
                        'lamp', 'floor_lamp', 'table_lamp', 'ceiling_light', 'chandelier',
                        
                        # Electronics
                        'tv', 'television', 'laptop', 'computer', 'monitor', 'speakers',
                        
                        # Decor & Accessories
                        'mirror', 'plant', 'potted_plant', 'vase', 'picture_frame', 'clock',
                        'book', 'pillow', 'rug', 'curtains',
                        
                        # Miscellaneous interior items
                        'ottoman', 'fireplace', 'radiator', 'air_conditioner'
                    }
                    
                    if label.lower() in furniture_objects or conf > 0.5:
                        # Convert to [x, y, width, height] format using validated coordinates
                        bbox_x = int(x1)
                        bbox_y = int(y1)
                        bbox_width = int(x2 - x1)  # These are now guaranteed positive due to validation above
                        bbox_height = int(y2 - y1)
                        
                        # Double-check dimensions are positive (should never trigger after validation)
                        if bbox_width <= 0 or bbox_height <= 0:
                            logger.error(f"Detected negative dimensions after validation: w={bbox_width}, h={bbox_height}")
                            continue
                        
                        # Canonical label mapping - normalize synonyms to standard categories
                        canonical_label = get_canonical_label(label.lower())
                        
                        objects.append({
                            "label": canonical_label,
                            "confidence": round(conf, 3),
                            "bbox": [bbox_x, bbox_y, bbox_width, bbox_height],
                            "area": int(bbox_width * bbox_height)
                        })
        
        # Sort by confidence and limit results
        objects.sort(key=lambda x: x['confidence'], reverse=True)
        return objects[:20]  # Top 20 objects
        
    except Exception as e:
        logger.error(f"Object detection failed: {e}")
        return []

def get_canonical_label(label: str) -> str:
    """
    Map YOLO labels to canonical furniture categories based on MODOMO_TAXONOMY.
    Handles synonyms and ensures consistent labeling.
    
    Args:
        label: YOLO detection label (lowercase)
        
    Returns:
        Canonical label from MODOMO_TAXONOMY
    """
    # Canonical label mapping - maps synonyms to standard categories
    label_mapping = {
        # Seating synonyms
        'couch': 'sofa',
        'settee': 'sofa', 
        'loveseat': 'sofa',
        'armchair': 'chair',
        'dining_chair': 'chair',
        'office_chair': 'chair',
        
        # Table synonyms  
        'dining_table': 'table',
        'coffee_table': 'table',
        'side_table': 'table',
        'end_table': 'table',
        'console_table': 'table',
        'desk': 'table',
        'nightstand': 'table',
        
        # Storage synonyms
        'bookshelf': 'shelf',
        'tv_stand': 'cabinet',
        'dresser': 'cabinet',
        'wardrobe': 'cabinet',
        
        # Electronics synonyms
        'television': 'tv',
        'monitor': 'tv',
        'computer': 'laptop',
        
        # Plant synonyms
        'potted_plant': 'plant',
        'houseplant': 'plant',
        
        # Lighting synonyms
        'floor_lamp': 'lamp',
        'table_lamp': 'lamp',
        'desk_lamp': 'lamp',
        
        # Kitchen synonyms
        'refrigerator': 'fridge',
        'stove': 'oven',
        'cooktop': 'oven'
    }
    
    # Return canonical label or original if no mapping exists
    return label_mapping.get(label, label)

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
            images=image,
            return_tensors="pt", 
            padding=True
        )
        
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
    
    # Define material taxonomy based on object types
    if material_taxonomy is None:
        material_taxonomy = {
            # Seating materials
            "sofa": ["fabric upholstery", "leather upholstery", "velvet fabric", "linen fabric", 
                    "microfiber", "wood frame", "metal legs"],
            "chair": ["wood", "metal", "plastic", "fabric seat", "leather seat", "rattan", "mesh"],
            
            # Table materials
            "table": ["wood surface", "glass top", "marble top", "metal frame", "laminate", 
                     "stone surface", "acrylic"],
            "desk": ["wood", "metal", "glass", "laminate", "particle board"],
            
            # Storage materials  
            "cabinet": ["wood", "metal", "laminate", "glass doors", "particle board", "MDF"],
            "shelf": ["wood", "metal", "glass", "wire mesh", "plastic"],
            "dresser": ["solid wood", "veneer", "laminate", "metal handles"],
            
            # Bedroom materials
            "bed": ["wood frame", "metal frame", "upholstered headboard", "fabric", "leather"],
            "mattress": ["memory foam", "latex", "spring coils", "fabric cover"],
            
            # Lighting materials
            "lamp": ["metal base", "ceramic base", "glass shade", "fabric shade", "plastic", "wood"],
            
            # Electronics
            "tv": ["plastic casing", "glass screen", "metal stand"],
            "monitor": ["plastic", "metal", "glass screen"],
            
            # Bathroom
            "toilet": ["ceramic", "porcelain", "plastic seat"],
            "bathtub": ["acrylic", "fiberglass", "cast iron", "ceramic"],
            "sink": ["ceramic", "porcelain", "stainless steel", "stone"],
            
            # Decor
            "mirror": ["glass", "metal frame", "wood frame", "plastic frame"],
            "plant": ["organic leaves", "ceramic pot", "plastic pot", "terracotta pot"],
            "vase": ["glass", "ceramic", "porcelain", "metal", "crystal"],
            "rug": ["wool", "cotton", "synthetic fiber", "jute", "silk"],
            "curtains": ["fabric", "polyester", "cotton", "linen", "silk"],
            "pillow": ["cotton cover", "linen", "velvet", "silk", "polyester fill"],
            
            # Default materials for unknown objects
            "default": ["wood", "metal", "fabric", "plastic", "glass", "ceramic"]
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
                
                # Prepare material prompts for CLIP
                material_prompts = [f"a photo of {mat}" for mat in material_candidates]
                
                if not material_prompts:
                    enhanced_obj["materials"] = []
                    enhanced_objects.append(enhanced_obj)
                    continue
                
                # Run CLIP on object crop with material prompts
                inputs = models['clip_processor'](
                    text=material_prompts,
                    images=object_crop,
                    return_tensors="pt",
                    padding=True
                )
                
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
    """Extract dominant colors from the image"""
    try:
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
            "palette_size": len(dominant_colors)
        }
        
    except Exception as e:
        logger.error(f"Color palette extraction failed: {e}")
        return {
            "dominant_colors": [],
            "palette_size": 0
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

def enhance_objects_with_details(image: Image.Image, objects: list) -> list:
    """
    Generate object thumbnails, descriptions, and depth crops for detected objects.
    
    Args:
        image: Original scene image
        objects: List of detected objects with bounding boxes
        
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
                
                # Generate depth crop if depth estimation was successful
                # Note: This would require passing depth map from estimate_depth function
                # For now, we'll mark it as a placeholder
                enhanced_obj["has_depth_crop"] = False  # Will be implemented when depth integration is added
                
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
        # Decode and load image
        image_bytes = base64.b64decode(image_data_b64)
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        logger.info(f"Processing scene {scene_id}, image size: {image.size}")
        
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
        logger.info("Running scene classification...")
        scene_analysis = classify_scene(image)
        results["scene_analysis"] = scene_analysis
        
        logger.info("Running object detection...")
        objects = detect_objects(image)
        results["objects_detected"] = len(objects)
        
        logger.info("Running object segmentation...")
        segmented_objects = segment_objects(image, objects)
        results["objects"] = segmented_objects
        
        logger.info("Running style analysis...")
        style_analysis = analyze_style(image)
        results["style_analysis"] = style_analysis
        
        logger.info("Running material analysis...")
        material_analysis = analyze_materials(image, segmented_objects)
        results["material_analysis"] = material_analysis
        
        logger.info("Generating object thumbnails and descriptions...")
        enhanced_objects = enhance_objects_with_details(image, segmented_objects)
        results["segmented_objects"] = enhanced_objects  # Replace with enhanced objects
        
        logger.info("Extracting color palette...")
        color_palette = extract_color_palette(image)
        results["color_palette"] = color_palette
        
        logger.info("Running depth estimation...")
        depth_analysis = estimate_depth(image)
        results["depth_analysis"] = depth_analysis
        
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
        processing_time = time.time() - start_time
        logger.error(f"❌ Scene processing failed after {processing_time:.2f}s: {e}")
        return {
            "status": "error",
            "error": str(e),
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
        enhanced = enhance_objects_with_details(img, materials)
        colors = extract_color_palette(img)
        depth = estimate_depth(img)
        
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
    
    with torch.no_grad():
        outputs = models['clip_model'](**inputs)
        logits = outputs.logits_per_image
        probs = logits.softmax(dim=1)
    
    results = []
    for i in range(len(images)):
        best_idx = probs[i].argmax().item()
        confidence = probs[i][best_idx].item()
        scene_type = scene_types[best_idx].replace("a ", "").replace(" interior", "")
        
        top_indices = probs[i].argsort(descending=True)[:3]
        alternatives = [
            {
                "type": scene_types[idx].replace("a ", "").replace(" interior", ""),
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
    """Batch object detection using YOLO."""
    # Convert PIL images to numpy arrays
    img_arrays = [np.array(img) for img in images]
    
    # Run batch inference
    batch_results = models['yolo'](img_arrays, conf=0.25, verbose=False)
    
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
                
                # Filter for furniture objects
                canonical_label = get_canonical_label(label.lower())
                
                objects.append({
                    "label": canonical_label,
                    "confidence": round(conf, 3),
                    "bbox": [int(x1), int(y1), int(x2 - x1), int(y2 - y1)],
                    "area": int((x2 - x1) * (y2 - y1))
                })
        
        objects.sort(key=lambda x: x['confidence'], reverse=True)
        all_objects.append(objects[:20])
    
    return all_objects

def _process_single_scene(image: Image.Image, scene_id: str, options: dict) -> dict:
    """Fallback to single scene processing."""
    try:
        # Use existing single-image functions
        scene_analysis = classify_scene(image)
        objects = detect_objects(image)
        segmented = segment_objects(image, objects)
        materials = detect_object_materials(image, segmented)
        enhanced = enhance_objects_with_details(image, materials)
        style = analyze_style(image)
        colors = extract_color_palette(image)
        depth = estimate_depth(image)
        
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
        
        # Health check
        if input_data.get("health_check"):
            return {
                "status": "success",
                "message": "Modomo AI pipeline is healthy",
                "models_loaded": len(models) > 0,
                "available_models": list(models.keys())
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