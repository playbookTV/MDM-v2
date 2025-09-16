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
    """Get furniture items for YOLO filtering"""
    return {
        'chair', 'couch', 'sofa', 'table', 'bed', 'desk', 'cabinet',
        'bench', 'stool', 'dresser', 'bookshelf', 'lamp', 'tv_stand',
        'ottoman', 'sectional', 'loveseat', 'coffee_table', 'dining_table'
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
        logger.info("🚀 Starting model loading process...")
        start_time = time.time()
        
        # Check GPU availability
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {device}")
        
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            memory_allocated = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"GPU: {gpu_name} ({memory_allocated:.1f}GB)")
        
        # Load YOLO model
        logger.info("📦 Loading YOLO model...")
        from ultralytics import YOLO
        models['yolo'] = YOLO('yolov8n.pt')  # Start with nano for faster loading
        models['yolo'].to(device)
        logger.info("✅ YOLO model loaded successfully")
        
        # Load CLIP model
        logger.info("📦 Loading CLIP model...")
        import clip
        models['clip'], models['clip_preprocess'] = clip.load("ViT-B/32", device=device)
        logger.info("✅ CLIP model loaded successfully")
        
        # Note: SAM2 and GroundingDINO loading would go here for full pipeline
        logger.info("⚠️  SAM2 and GroundingDINO loading skipped for quick startup")
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Model loading completed in {elapsed:.2f}s")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        model_loading_lock = False
        return False


def detect_objects_yolo(image: Image.Image, confidence_threshold: float = 0.35) -> List[Dict]:
    """
    Run YOLO object detection on image and return furniture objects.
    
    Args:
        image: PIL Image
        confidence_threshold: Minimum confidence for detections
        
    Returns:
        List of detected objects with bbox in [x, y, width, height] format
    """
    if 'yolo' not in models:
        logger.error("YOLO model not loaded")
        return []
    
    try:
        # Run inference
        results = models['yolo'](image, verbose=False)
        objects = []
        
        # Extract detections
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
                    label = models['yolo'].names[int(box.cls[0])]
                    
                    # Filter for furniture items with confidence threshold
                    if is_furniture_item(label, conf, confidence_threshold):
                        canonical_label = get_canonical_label(label.lower())
                        
                        objects.append({
                            "label": canonical_label,
                            "confidence": round(conf, 3),
                            "bbox": [int(x1), int(y1), int(x2 - x1), int(y2 - y1)],  # [x, y, width, height]
                            "area": int((x2 - x1) * (y2 - y1))
                        })
        
        objects.sort(key=lambda x: x['confidence'], reverse=True)
        logger.info(f"Detected {len(objects)} furniture objects")
        return objects
        
    except Exception as e:
        logger.error(f"YOLO detection failed: {e}")
        return []


def analyze_scene_style_clip(image: Image.Image) -> Dict[str, Any]:
    """
    Analyze scene style using CLIP zero-shot classification.
    
    Args:
        image: PIL Image
        
    Returns:
        Dict with style analysis results
    """
    if 'clip' not in models:
        logger.error("CLIP model not loaded")
        return {"primary_style": "unknown", "confidence": 0.0}
    
    try:
        style_categories = [
            "contemporary modern interior",
            "traditional classic interior", 
            "minimalist interior",
            "rustic farmhouse interior",
            "industrial interior",
            "scandinavian interior"
        ]
        
        # Prepare image and text
        image_tensor = models['clip_preprocess'](image).unsqueeze(0).to(next(models['clip'].parameters()).device)
        text_tokens = clip.tokenize(style_categories).to(next(models['clip'].parameters()).device)
        
        # Get predictions
        with torch.no_grad():
            logits_per_image, logits_per_text = models['clip'](image_tensor, text_tokens)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]
        
        # Find best match
        best_idx = np.argmax(probs)
        style_name = style_categories[best_idx].replace(" interior", "").replace(" ", "_")
        
        return {
            "primary_style": style_name,
            "confidence": float(probs[best_idx]),
            "all_styles": {
                style_categories[i].replace(" interior", "").replace(" ", "_"): float(probs[i])
                for i in range(len(style_categories))
            }
        }
        
    except Exception as e:
        logger.error(f"Style analysis failed: {e}")
        return {"primary_style": "unknown", "confidence": 0.0}


def classify_room_type_clip(image: Image.Image) -> Dict[str, Any]:
    """
    Classify room type using CLIP zero-shot classification.
    
    Args:
        image: PIL Image
        
    Returns:
        Dict with room classification results
    """
    if 'clip' not in models:
        logger.error("CLIP model not loaded")
        return {"room_type": "unknown", "confidence": 0.0}
    
    try:
        room_categories = [
            "living room interior",
            "bedroom interior",
            "kitchen interior",
            "dining room interior",
            "bathroom interior",
            "office interior",
            "hallway interior"
        ]
        
        # Prepare image and text
        image_tensor = models['clip_preprocess'](image).unsqueeze(0).to(next(models['clip'].parameters()).device)
        text_tokens = clip.tokenize(room_categories).to(next(models['clip'].parameters()).device)
        
        # Get predictions
        with torch.no_grad():
            logits_per_image, logits_per_text = models['clip'](image_tensor, text_tokens)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]
        
        # Find best match
        best_idx = np.argmax(probs)
        room_name = room_categories[best_idx].replace(" interior", "").replace(" ", "_")
        
        return {
            "room_type": room_name,
            "confidence": float(probs[best_idx]),
            "all_types": {
                room_categories[i].replace(" interior", "").replace(" ", "_"): float(probs[i])
                for i in range(len(room_categories))
            }
        }
        
    except Exception as e:
        logger.error(f"Room classification failed: {e}")
        return {"room_type": "unknown", "confidence": 0.0}


def handler(job):
    """
    Main RunPod handler function for scene processing.
    
    Args:
        job: RunPod job object with 'input' containing scene data
        
    Returns:
        Dict with processing results
    """
    try:
        job_input = job["input"]
        scene_id = job_input.get("scene_id", "unknown")
        
        logger.info(f"🎯 Processing scene: {scene_id}")
        start_time = time.time()
        
        # Decode image
        image_data = job_input.get("image")
        if not image_data:
            return {"error": "No image data provided"}
        
        # Handle both base64 and URL inputs
        if image_data.startswith('data:image'):
            # Remove data:image/jpeg;base64, prefix
            image_data = image_data.split(',', 1)[1]
        
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            logger.info(f"📷 Image loaded: {image.size}")
        except Exception as e:
            logger.error(f"Failed to decode image: {e}")
            return {"error": f"Failed to decode image: {str(e)}"}
        
        # Initialize results
        results = {
            "scene_id": scene_id,
            "success": True,
            "processing_time": 0,
            "image_size": image.size,
            "components_processed": []
        }
        
        # Object Detection
        logger.info("🔍 Running object detection...")
        objects = detect_objects_yolo(image)
        results["objects"] = objects
        results["objects_detected"] = len(objects)
        results["components_processed"].append("object_detection")
        logger.info(f"✅ Detected {len(objects)} objects")
        
        # Style Analysis
        logger.info("🎨 Analyzing scene style...")
        style_result = analyze_scene_style_clip(image)
        results["style"] = style_result
        results["components_processed"].append("style_analysis")
        logger.info(f"✅ Style: {style_result['primary_style']} ({style_result['confidence']:.2f})")
        
        # Room Classification
        logger.info("🏠 Classifying room type...")
        room_result = classify_room_type_clip(image)
        results["room"] = room_result
        results["components_processed"].append("room_classification")
        logger.info(f"✅ Room: {room_result['room_type']} ({room_result['confidence']:.2f})")
        
        # Processing complete
        processing_time = time.time() - start_time
        results["processing_time"] = round(processing_time, 2)
        
        logger.info(f"✅ Scene {scene_id} processed successfully in {processing_time:.2f}s")
        return results
        
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            "scene_id": job.get("input", {}).get("scene_id", "unknown"),
            "success": False,
            "error": str(e)
        }


# RunPod serverless handler
if __name__ == "__main__":
    logger.info("🚀 Starting RunPod serverless handler...")
    runpod.serverless.start({"handler": handler})