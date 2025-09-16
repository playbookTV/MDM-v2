"""
AI Pipeline Service for scene analysis using real models
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
try:
    import numpy as np
    from PIL import Image
    import io
    HAS_IMAGING = True
except ImportError:
    logger.warning("PIL/numpy not available - using mocks only")
    HAS_IMAGING = False
    Image = None
    io = None
    np = None

from app.core.config import settings
from app.core.taxonomy import get_canonical_label, is_furniture_item, get_category_for_item

logger = logging.getLogger(__name__)

# AI models should be deployed on RunPod, not locally
AI_MODELS_AVAILABLE = False  # Force use of RunPod only
logger.info("AI models configured for RunPod deployment - no local models loaded")


class AIModelManager:
    """Manages loading and caching of AI models"""
    
    def __init__(self):
        self.models = {}
        self.processors = {}
        self._initialized = False
    
    async def initialize_models(self):
        """Initialize AI models (RunPod deployment - no local models)"""
        logger.info("AI models are deployed on RunPod - no local initialization needed")
        self._initialized = False  # Always use RunPod


class AIPipelineService:
    """Complete AI pipeline for scene analysis"""
    
    def __init__(self):
        self.model_manager = AIModelManager()
        
        # Scene type labels for classification
        self.scene_types = [
            "living room", "bedroom", "kitchen", "bathroom", "dining room",
            "office", "hallway", "outdoor", "garage", "basement"
        ]
        
        # Style classification labels
        self.design_styles = [
            "contemporary", "traditional", "modern", "rustic", "industrial",
            "scandinavian", "minimalist", "bohemian", "art deco", "farmhouse"
        ]
    
    def _normalize_scene_type(self, scene_type: str) -> str:
        """Normalize scene type to match database schema"""
        if not scene_type:
            return "unknown"
        
        # Convert to lowercase and replace spaces with underscores
        normalized = scene_type.lower().replace(" ", "_").replace("-", "_")
        
        # Map common variations to our canonical forms
        scene_type_mapping = {
            "living_room": "living_room",
            "dining_room": "dining_room", 
            "bed_room": "bedroom",
            "bath_room": "bathroom",
            "home_office": "office",
            "work_space": "office",
            "corridor": "hallway",
            "entrance": "hallway",
            "patio": "outdoor",
            "garden": "outdoor",
            "terrace": "balcony"
        }
        
        # Return mapped value or normalized value if no mapping exists
        return scene_type_mapping.get(normalized, normalized)
    
    def _normalize_style_type(self, style_type: str) -> str:
        """Normalize style type to match database schema"""
        if not style_type:
            return "contemporary"
        
        # Convert to lowercase and replace spaces/hyphens with underscores
        normalized = style_type.lower().replace(" ", "_").replace("-", "_")
        
        # Map common variations to our canonical forms
        style_type_mapping = {
            "mid_century": "mid_century",
            "midcentury": "mid_century",
            "scandinavian": "scandi",
            "minimalist": "minimal",
            "luxurious": "luxe",
            "eclectic_mix": "eclectic",
            "coastal_style": "coastal"
        }
        
        # Return mapped value or normalized value if no mapping exists
        return style_type_mapping.get(normalized, normalized)
    
    def _process_detected_objects(self, raw_objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and filter detected objects using centralized taxonomy"""
        processed_objects = []
        
        for obj in raw_objects:
            # Get original detection data
            label = obj.get('class', obj.get('label', ''))
            confidence = obj.get('confidence', obj.get('conf', 0.0))
            bbox = obj.get('bbox', obj.get('box', []))
            
            # Skip if no label or confidence too low
            if not label or confidence < 0.1:
                continue
            
            # Apply taxonomy filtering
            if not is_furniture_item(label, confidence):
                logger.debug(f"Filtered out non-furniture item: {label} (conf: {confidence:.3f})")
                continue
            
            # Get canonical label and category
            canonical_label = get_canonical_label(label)
            category = get_category_for_item(canonical_label)
            
            # Create processed object with canonical labels
            processed_obj = {
                'label': canonical_label,
                'original_label': label,
                'category': category,
                'confidence': confidence,
                'bbox': bbox,
                'bbox_format': obj.get('bbox_format')
            }
            
            # Preserve additional fields from original object
            for field in ['mask_url', 'mask_base64', 'segmentation', 'area', 'material', 'description']:
                if field in obj:
                    processed_obj[field] = obj[field]
            
            processed_objects.append(processed_obj)
            logger.debug(f"Processed object: '{label}' -> '{canonical_label}' ({category}, conf: {confidence:.3f})")
        
        logger.info(f"Taxonomy filtering: {len(raw_objects)} -> {len(processed_objects)} objects retained")
        return processed_objects
    
    async def process_scene(
        self, 
        image_data: bytes, 
        scene_id: str,
        options: Dict[str, Any] = None,
        skip_ai: Dict[str, bool] = None
    ) -> Dict[str, Any]:
        """
        Complete scene processing pipeline
        
        Args:
            image_data: Raw image bytes
            scene_id: Unique scene identifier
            options: Processing options
            skip_ai: Dict indicating which AI components to skip (from pre-existing metadata)
            
        Returns:
            Dictionary with all analysis results
        """
        logger.info(f"Starting AI pipeline for scene {scene_id}")
        
        # Initialize skip_ai if not provided
        if skip_ai is None:
            skip_ai = {}
            
        # Log which components will be skipped
        skipped_components = [k for k, v in skip_ai.items() if v]
        if skipped_components:
            logger.info(f"Scene {scene_id}: Skipping AI processing for: {', '.join(skipped_components)}")
        else:
            logger.info(f"Scene {scene_id}: Full AI processing will be performed")
        
        # Process with RunPod - no fallback allowed
        if not settings.AI_PROCESSING_ENABLED:
            raise RuntimeError(f"AI processing is disabled for scene {scene_id}. RunPod processing is required.")
            
        runpod_result = await self._try_runpod_processing(image_data, scene_id, options, skip_ai)
        logger.info(f"RunPod result for scene {scene_id}: success={runpod_result.get('success')}, status={runpod_result.get('status')}")
        
        if runpod_result.get("success"):
            logger.info(f"✅ RunPod processing completed for scene {scene_id}: {runpod_result.get('scene_type')} ({runpod_result.get('scene_conf', 0):.2f})")
            return runpod_result
        else:
            error_msg = f"RunPod processing failed for scene {scene_id}: {runpod_result.get('error')}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def _try_runpod_processing(
        self, 
        image_data: bytes, 
        scene_id: str,
        options: Dict[str, Any] = None,
        skip_ai: Dict[str, bool] = None
    ) -> Dict[str, Any]:
        """Try processing with RunPod"""
        try:
            from app.services.runpod_client import runpod_client
            
            if not runpod_client.is_configured():
                return {
                    "success": False,
                    "error": "RunPod not configured"
                }
            
            logger.info(f"Processing scene {scene_id} with RunPod...")
            
            # Add skip_ai to options for RunPod processing
            runpod_options = (options or {}).copy()
            if skip_ai:
                runpod_options["skip_ai"] = skip_ai
                skipped_components = [k for k, v in skip_ai.items() if v]
                if skipped_components:
                    logger.info(f"Scene {scene_id}: Passing skip_ai to RunPod: {', '.join(skipped_components)}")
            
            result = await runpod_client.process_scene_runpod(image_data, scene_id, runpod_options)
            
            if result.get("status") == "success":
                # Transform RunPod result to our expected format
                runpod_output = result.get("result", {})
                logger.info(f"RunPod output keys for scene {scene_id}: {list(runpod_output.keys())}")
                logger.info(f"RunPod objects count: {len(runpod_output.get('objects', []))}")
                
                # Process detected objects with taxonomy filtering
                raw_objects = runpod_output.get('objects', [])
                processed_objects = self._process_detected_objects(raw_objects)

                # Extract image size when provided by RunPod (width, height)
                image_size = runpod_output.get('image_size')
                if isinstance(image_size, (list, tuple)) and len(image_size) == 2:
                    image_width = int(image_size[0])
                    image_height = int(image_size[1])
                else:
                    image_width = image_height = None
                
                # Parse scene analysis
                scene_analysis = runpod_output.get('scene_analysis', {})
                raw_scene_type = scene_analysis.get('scene_type', 'unknown')
                scene_type = self._normalize_scene_type(raw_scene_type)
                scene_conf = scene_analysis.get('confidence', 0.0)
                logger.info(f"Scene type normalized: '{raw_scene_type}' -> '{scene_type}'")
                
                # Parse style analysis
                style_analysis = runpod_output.get('style_analysis', {})
                raw_primary_style = style_analysis.get('primary_style', 'contemporary')
                primary_style = self._normalize_style_type(raw_primary_style)
                style_confidence = style_analysis.get('style_confidence', 0.0)
                logger.info(f"Style normalized: '{raw_primary_style}' -> '{primary_style}'")
                
                # Parse color palette  
                color_palette = runpod_output.get('color_palette', {})
                dominant_colors = color_palette.get('dominant_colors', [])
                
                # Prepare palette in database format: [{"hex": "#aabbcc", "p": 0.23}, ...]
                palette_for_db = []
                dominant_color = {'r': 128, 'g': 128, 'b': 128, 'hex': '#808080'}  # Default
                
                if dominant_colors and len(dominant_colors) > 0:
                    for color_info in dominant_colors:
                        if 'hex' in color_info and 'frequency' in color_info:
                            palette_for_db.append({
                                'hex': color_info['hex'],
                                'p': color_info['frequency']
                            })
                    
                    # Set dominant color (first one) for backwards compatibility
                    first_color = dominant_colors[0]
                    if 'rgb' in first_color:
                        rgb = first_color['rgb']
                        dominant_color = {
                            'r': rgb[0], 'g': rgb[1], 'b': rgb[2], 
                            'hex': first_color.get('hex', f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}")
                        }
                
                # Parse depth analysis (preserve base64 if provided by RunPod)
                depth_analysis = runpod_output.get('depth_analysis', {})
                depth_available = depth_analysis.get('depth_available', False)
                depth_base64 = depth_analysis.get('depth_base64')
                
                # Optional generated assets
                thumbnail_base64 = runpod_output.get('thumbnail_base64')
                
                return {
                    'scene_id': scene_id,
                    'processing_started': datetime.utcnow().isoformat(),
                    'status': 'completed',
                    'success': True,
                    'processed_with': 'runpod',
                    **({'width': image_width, 'height': image_height} if image_width is not None and image_height is not None else {}),
                    'scene_type': scene_type,
                    'scene_conf': scene_conf,
                    'objects_detected': len(processed_objects),
                    'objects': processed_objects,  # Use taxonomy-filtered objects
                    'raw_objects_count': len(raw_objects),  # Track filtering effectiveness
                    'primary_style': primary_style,
                    'style_confidence': style_confidence,
                    'depth_available': depth_available,
                    # Pass through base64 blobs so worker can upload
                    **({'thumbnail_base64': thumbnail_base64} if thumbnail_base64 else {}),
                    **({'depth_analysis': {**depth_analysis, **({'depth_base64': depth_base64} if depth_base64 else {})}} if depth_analysis else {}),
                    'dominant_color': dominant_color,  # Keep for backwards compatibility
                    'color_palette': palette_for_db,  # Full palette for frontend
                    'processing_completed': datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "RunPod processing failed")
                }
                
        except ImportError:
            logger.warning("RunPod client not available")
            return {
                "success": False,
                "error": "RunPod client not available"
            }
        except Exception as e:
            logger.error(f"RunPod processing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global pipeline instance
ai_pipeline = AIPipelineService()


async def process_scene_ai(image_data: bytes, scene_id: str, options: Dict[str, Any] = None, skip_ai: Dict[str, bool] = None) -> Dict[str, Any]:
    """
    Main entry point for scene AI processing
    
    Args:
        image_data: Raw image bytes
        scene_id: Unique scene identifier  
        options: Processing options
        skip_ai: Dict indicating which AI components to skip (from pre-existing metadata)
        
    Returns:
        Complete AI analysis results
    """
    return await ai_pipeline.process_scene(image_data, scene_id, options, skip_ai)
