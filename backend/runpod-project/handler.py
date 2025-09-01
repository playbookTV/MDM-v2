"""
Production RunPod Handler for Modomo AI Pipeline
Handles interior design scene analysis with YOLO, CLIP, and depth estimation
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
        from sam2.build_sam import build_sam2
        from sam2.sam2_image_predictor import SAM2ImagePredictor
        sam2_checkpoint = "facebook/sam2-hiera-large"
        sam2_model_cfg = "sam2_hiera_l.yaml"
        models['sam2_predictor'] = SAM2ImagePredictor(build_sam2(sam2_model_cfg, sam2_checkpoint))
        logger.info("✅ SAM2 loaded")
        
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
        
        return {
            "depth_available": True,
            "depth_stats": {
                "min_depth": float(depth_array.min()),
                "max_depth": float(depth_array.max()), 
                "mean_depth": float(depth_array.mean()),
                "depth_range": float(depth_array.max() - depth_array.min())
            }
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
        
        results = {
            "scene_id": scene_id,
            "processing_started": time.time(),
            "image_size": image.size
        }
        
        # Run AI analysis pipeline
        logger.info("Running scene classification...")
        scene_analysis = classify_scene(image)
        results["scene_analysis"] = scene_analysis
        
        logger.info("Running object detection...")
        objects = detect_objects(image)
        results["objects"] = objects
        results["objects_detected"] = len(objects)
        
        logger.info("Running style analysis...")
        style_analysis = analyze_style(image)
        results["style_analysis"] = style_analysis
        
        logger.info("Running depth estimation...")
        depth_analysis = estimate_depth(image)
        results["depth_analysis"] = depth_analysis
        
        # Processing complete
        processing_time = time.time() - start_time
        results["processing_time"] = round(processing_time, 2)
        results["processing_completed"] = time.time()
        
        logger.info(f"✅ Scene {scene_id} processed in {processing_time:.2f}s")
        logger.info(f"   Scene: {scene_analysis['scene_type']} ({scene_analysis['confidence']:.2f})")
        logger.info(f"   Objects: {len(objects)}")
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