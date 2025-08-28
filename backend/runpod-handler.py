"""
RunPod Serverless Handler for Modomo AI Pipeline
Handles image processing requests with YOLO, SAM2, Depth Anything, and CLIP
"""

import runpod
import torch
import base64
import io
import json
import logging
from PIL import Image
import numpy as np
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model instances (loaded once)
models = {}

def load_models():
    """Load all AI models into memory"""
    try:
        logger.info("Loading AI models...")
        
        # Load YOLOv8 for object detection
        from ultralytics import YOLO
        models['yolo'] = YOLO('yolov8n.pt')  # Start with nano, can upgrade to larger models
        logger.info("✅ YOLOv8 loaded")
        
        # Load SAM2 for segmentation
        from segment_anything import SamPredictor, sam_model_registry
        sam = sam_model_registry["vit_h"](checkpoint="sam_vit_h_4b8939.pth")
        models['sam'] = SamPredictor(sam)
        logger.info("✅ SAM2 loaded")
        
        # Load Depth Anything for depth estimation
        from depth_anything import DepthAnything
        models['depth'] = DepthAnything.from_pretrained('LiheYoung/depth_anything_vitl14')
        logger.info("✅ Depth Anything loaded")
        
        # Load CLIP for embeddings and zero-shot classification
        import clip
        models['clip'], models['clip_preprocess'] = clip.load("ViT-B/32", device="cuda")
        logger.info("✅ CLIP loaded")
        
        logger.info("🎉 All models loaded successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error loading models: {e}")
        raise

def process_image(image_data: str) -> Dict[str, Any]:
    """Process image through the complete AI pipeline"""
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        image_array = np.array(image)
        
        results = {
            "scene_analysis": {},
            "objects": [],
            "depth_map": None,
            "processing_time": 0
        }
        
        # 1. Object Detection with YOLO
        logger.info("Detecting objects with YOLO...")
        yolo_results = models['yolo'](image_array, conf=0.25)
        
        objects = []
        for detection in yolo_results[0].boxes.data:
            x1, y1, x2, y2, conf, cls = detection.cpu().numpy()
            
            # Get SAM2 segmentation for this object
            bbox = np.array([x1, y1, x2, y2])
            models['sam'].set_image(image_array)
            masks, scores, _ = models['sam'].predict(
                box=bbox,
                multimask_output=True
            )
            
            # Use best mask
            best_mask_idx = np.argmax(scores)
            mask = masks[best_mask_idx]
            
            # Get CLIP embeddings for zero-shot classification
            cropped_object = image.crop((int(x1), int(y1), int(x2), int(y2)))
            clip_input = models['clip_preprocess'](cropped_object).unsqueeze(0).cuda()
            
            # Define furniture categories
            furniture_categories = [
                "chair", "table", "sofa", "bed", "lamp", "cabinet", 
                "desk", "shelf", "mirror", "rug", "curtain", "plant"
            ]
            
            with torch.no_grad():
                image_features = models['clip'].encode_image(clip_input)
                text_features = models['clip'].encode_text(
                    clip.tokenize(furniture_categories).cuda()
                )
                
                # Calculate similarities
                similarities = torch.cosine_similarity(image_features, text_features)
                best_category_idx = similarities.argmax().item()
                confidence = similarities[best_category_idx].item()
                
            objects.append({
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "confidence": float(conf),
                "category": furniture_categories[best_category_idx],
                "category_confidence": confidence,
                "mask": mask.tolist()  # Convert numpy array to list for JSON
            })
        
        results["objects"] = objects
        
        # 2. Depth Estimation
        logger.info("Generating depth map...")
        depth_input = models['clip_preprocess'](image).unsqueeze(0).cuda()
        with torch.no_grad():
            depth_map = models['depth'](depth_input)
            depth_map = depth_map.squeeze().cpu().numpy()
            # Normalize depth map for visualization
            depth_map = ((depth_map - depth_map.min()) / (depth_map.max() - depth_map.min()) * 255).astype(np.uint8)
            results["depth_map"] = base64.b64encode(depth_map.tobytes()).decode()
        
        # 3. Scene Classification (using CLIP)
        logger.info("Classifying scene...")
        scene_prompts = [
            "a bedroom", "a living room", "a kitchen", "a bathroom", 
            "a dining room", "an office", "a hallway", "a study"
        ]
        
        with torch.no_grad():
            text_features = models['clip'].encode_text(
                clip.tokenize(scene_prompts).cuda()
            )
            similarities = torch.cosine_similarity(image_features, text_features)
            best_scene_idx = similarities.argmax().item()
            scene_confidence = similarities[best_scene_idx].item()
            
        results["scene_analysis"] = {
            "scene_type": scene_prompts[best_scene_idx],
            "confidence": scene_confidence
        }
        
        logger.info(f"✅ Processed image: {len(objects)} objects detected")
        return {
            "status": "success",
            "result": results
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing image: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def handler(event):
    """Main handler function for RunPod serverless"""
    try:
        # Load models if not already loaded
        if not models:
            load_models()
        
        # Extract input
        input_data = event.get("input", {})
        image_data = input_data.get("image")
        
        if not image_data:
            return {
                "status": "error",
                "error": "No image data provided"
            }
        
        # Process the image
        result = process_image(image_data)
        return result
        
    except Exception as e:
        logger.error(f"❌ Handler error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# Start the serverless handler
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})

