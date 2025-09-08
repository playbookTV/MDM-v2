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
                    # Extract box data
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = models['yolo'].names[cls]
                    
                    # Filter for furniture/interior objects
                    furniture_objects = {
                        'chair', 'couch', 'potted plant', 'bed', 'dining table',
                        'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard',
                        'cell phone', 'microwave', 'oven', 'toaster', 'sink',
                        'refrigerator', 'book', 'clock', 'vase', 'scissors',
                        'teddy bear', 'hair drier', 'toothbrush', 'sofa', 'table'
                    }
                    
                    if label.lower() in furniture_objects or conf > 0.5:
                        objects.append({
                            "label": label,
                            "confidence": round(conf, 3),
                            "bbox": [int(x1), int(y1), int(x2), int(y2)],
                            "area": int((x2-x1) * (y2-y1))
                        })
        
        # Sort by confidence and limit results
        objects.sort(key=lambda x: x['confidence'], reverse=True)
        return objects[:20]  # Top 20 objects
        
    except Exception as e:
        logger.error(f"Object detection failed: {e}")
        return []

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
                bbox = obj['bbox']
                center_x = int((bbox[0] + bbox[2]) / 2)
                center_y = int((bbox[1] + bbox[3]) / 2)
                
                # Generate mask using point prompt
                masks, scores, _ = models['sam2_predictor'].predict(
                    point_coords=np.array([[center_x, center_y]]),
                    point_labels=np.array([1]),
                    multimask_output=True
                )
                
                # Use the best mask (highest score)
                best_mask_idx = np.argmax(scores)
                mask = masks[best_mask_idx]
                
                # Calculate mask statistics
                mask_area = int(np.sum(mask))
                mask_coverage = mask_area / (image.size[0] * image.size[1])
                
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
                bbox = obj['bbox']
                # Convert to input format for transformers SAM2 (4 levels required)
                # Format: [image level, object level, point level, point coordinates]
                input_points = [[[[int((bbox[0] + bbox[2]) / 2), int((bbox[1] + bbox[3]) / 2)]]]]
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
                
                # Calculate mask statistics
                mask_area = int(np.sum(mask))
                mask_coverage = mask_area / (image.size[0] * image.size[1])
                
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

def analyze_materials(image: Image.Image, objects: list) -> dict:
    """Analyze materials using CLIP zero-shot classification"""
    try:
        material_prompts = [
            "wood material", "metal material", "fabric material", "leather material",
            "glass material", "ceramic material", "plastic material", "stone material"
        ]
        
        inputs = models['clip_processor'](
            text=material_prompts,
            images=image,
            return_tensors="pt",
            padding=True
        )
        
        with torch.no_grad():
            outputs = models['clip_model'](**inputs)
            logits = outputs.logits_per_image
            probs = logits.softmax(dim=1)
        
        # Get detected materials
        materials = []
        for i, material in enumerate(material_prompts):
            confidence = float(probs[0][i])
            if confidence > 0.15:  # Only confident predictions
                materials.append({
                    "material": material.replace(" material", ""),
                    "confidence": round(confidence, 3)
                })
        
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

def handler(event):
    """Main RunPod serverless handler"""
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
        
        # Main processing
        image_data = input_data.get("image")
        scene_id = input_data.get("scene_id", f"scene_{int(time.time())}")
        options = input_data.get("options", {})
        
        if not image_data:
            return {
                "status": "error",
                "error": "No image data provided. Send base64 encoded image in 'image' field."
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