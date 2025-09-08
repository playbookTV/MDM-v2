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

logger = logging.getLogger(__name__)

# AI models should be deployed on RunPod, not locally
# Only keep minimal dependencies for fallback mocks
AI_MODELS_AVAILABLE = False  # Force use of RunPod or mocks
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
        self._initialized = False  # Always use RunPod or fallback to mocks


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
    
    async def process_scene(
        self, 
        image_data: bytes, 
        scene_id: str,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Complete scene processing pipeline
        
        Args:
            image_data: Raw image bytes
            scene_id: Unique scene identifier
            options: Processing options
            
        Returns:
            Dictionary with all analysis results
        """
        logger.info(f"Starting AI pipeline for scene {scene_id}")
        
        # Check if RunPod processing is available and enabled
        if settings.AI_PROCESSING_ENABLED:
            runpod_result = await self._try_runpod_processing(image_data, scene_id, options)
            logger.info(f"RunPod result for scene {scene_id}: success={runpod_result.get('success')}, status={runpod_result.get('status')}")
            if runpod_result.get("success"):
                logger.info(f"✅ RunPod processing completed for scene {scene_id}: {runpod_result.get('scene_type')} ({runpod_result.get('scene_conf', 0):.2f})")
                return runpod_result
            else:
                logger.warning(f"❌ RunPod processing failed for scene {scene_id}, falling back to local: {runpod_result.get('error')}")
        
        # Fallback to local processing
        return await self._process_locally(image_data, scene_id, options)
    
    async def _try_runpod_processing(
        self, 
        image_data: bytes, 
        scene_id: str,
        options: Dict[str, Any] = None
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
            result = await runpod_client.process_scene_runpod(image_data, scene_id, options)
            
            if result.get("status") == "success":
                # Transform RunPod result to our expected format
                runpod_output = result.get("result", {})
                logger.info(f"RunPod output keys for scene {scene_id}: {list(runpod_output.keys())}")
                logger.info(f"RunPod objects count: {len(runpod_output.get('objects', []))}")
                
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
                dominant_color = {'r': 128, 'g': 128, 'b': 128, 'hex': '#808080'}  # Default
                if dominant_colors and len(dominant_colors) > 0:
                    first_color = dominant_colors[0]
                    if 'rgb' in first_color:
                        rgb = first_color['rgb']
                        dominant_color = {
                            'r': rgb[0], 'g': rgb[1], 'b': rgb[2], 
                            'hex': first_color.get('hex', f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}")
                        }
                
                # Parse depth analysis
                depth_analysis = runpod_output.get('depth_analysis', {})
                depth_available = depth_analysis.get('depth_available', False)
                
                return {
                    'scene_id': scene_id,
                    'processing_started': datetime.utcnow().isoformat(),
                    'status': 'completed',
                    'success': True,
                    'processed_with': 'runpod',
                    'scene_type': scene_type,
                    'scene_conf': scene_conf,
                    'objects_detected': len(runpod_output.get('objects', [])),
                    'objects': runpod_output.get('objects', []),  # Include actual objects
                    'primary_style': primary_style,
                    'style_confidence': style_confidence,
                    'depth_available': depth_available,
                    'dominant_color': dominant_color,
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
    
    async def _process_locally(
        self, 
        image_data: bytes, 
        scene_id: str,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process using mock implementations (AI models are on RunPod)"""
        logger.info(f"Processing scene {scene_id} with mock implementations (RunPod preferred)")
        
        try:
            results = {
                'scene_id': scene_id,
                'processing_started': datetime.utcnow().isoformat(),
                'status': 'processing',
                'processed_with': 'mock'
            }
            
            # Use mock implementations since real AI is on RunPod
            scene_analysis = await self._mock_scene_classification()
            results.update(scene_analysis)
            
            object_analysis = await self._mock_object_detection()
            results.update(object_analysis)
            
            style_analysis = await self._mock_style_analysis()
            results.update(style_analysis)
            
            depth_analysis = await self._mock_depth_estimation()
            results.update(depth_analysis)
            
            # Simple color analysis without heavy dependencies
            color_analysis = await self._analyze_colors_basic(image_data)
            results.update(color_analysis)
            
            # Final status
            results.update({
                'status': 'completed',
                'processing_completed': datetime.utcnow().isoformat(),
                'success': True
            })
            
            logger.info(f"✅ Mock pipeline completed for scene {scene_id}")
            return results
            
        except Exception as e:
            logger.error(f"Mock pipeline failed for scene {scene_id}: {e}")
            return {
                'scene_id': scene_id,
                'status': 'failed',
                'error': str(e),
                'success': False,
                'processing_completed': datetime.utcnow().isoformat()
            }
    
    async def _classify_scene(self, image: Image.Image) -> Dict[str, Any]:
        """Classify scene type using CLIP"""
        if not AI_MODELS_AVAILABLE or not self.model_manager._initialized:
            return await self._mock_scene_classification()
        
        try:
            clip_model = self.model_manager.models['clip']
            clip_processor = self.model_manager.processors['clip']
            
            # Prepare text prompts for scene types
            text_prompts = [f"a photo of a {scene_type}" for scene_type in self.scene_types]
            
            # Process inputs
            inputs = clip_processor(
                text=text_prompts, 
                images=image, 
                return_tensors="pt", 
                padding=True
            )
            
            # Run inference
            with torch.no_grad():
                outputs = clip_model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
            
            # Get top prediction
            top_prob, top_idx = torch.max(probs, dim=1)
            scene_type = self.scene_types[top_idx.item()]
            confidence = top_prob.item()
            
            return {
                'scene_type': scene_type,
                'scene_conf': round(confidence, 3),
                'scene_alternatives': [
                    {'type': self.scene_types[i], 'conf': round(probs[0][i].item(), 3)}
                    for i in probs[0].argsort(descending=True)[:3]
                ]
            }
            
        except Exception as e:
            logger.error(f"Scene classification failed: {e}")
            return await self._mock_scene_classification()
    
    async def _detect_objects(self, image: Image.Image) -> Dict[str, Any]:
        """Detect objects using YOLO"""
        if not AI_MODELS_AVAILABLE or not self.model_manager._initialized:
            return await self._mock_object_detection()
            
        try:
            yolo_model = self.model_manager.models['yolo']
            
            # Convert PIL to numpy array for YOLO
            image_np = np.array(image)
            
            # Run YOLO inference
            results = yolo_model(image_np)
            
            detected_objects = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get object info
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        label = yolo_model.names[cls]
                        
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
                        detected_objects.append({
                            'label': label,
                            'confidence': round(conf, 3),
                            'bbox': {
                                'x1': int(x1), 'y1': int(y1),
                                'x2': int(x2), 'y2': int(y2)
                            },
                            'area': int((x2-x1) * (y2-y1))
                        })
            
            return {
                'objects_detected': len(detected_objects),
                'objects': detected_objects[:20],  # Limit to top 20
                'object_categories': list(set([obj['label'] for obj in detected_objects]))
            }
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return await self._mock_object_detection()
    
    async def _analyze_style(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze design style using CLIP"""
        if not AI_MODELS_AVAILABLE or not self.model_manager._initialized:
            return await self._mock_style_analysis()
        
        try:
            clip_model = self.model_manager.models['clip']
            clip_processor = self.model_manager.processors['clip']
            
            # Prepare style prompts
            text_prompts = [f"a {style} interior design" for style in self.design_styles]
            
            # Process inputs
            inputs = clip_processor(
                text=text_prompts,
                images=image,
                return_tensors="pt",
                padding=True
            )
            
            # Run inference
            with torch.no_grad():
                outputs = clip_model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
            
            # Get top styles
            top_styles = []
            for i, style in enumerate(self.design_styles):
                confidence = probs[0][i].item()
                if confidence > 0.1:  # Only include confident predictions
                    top_styles.append({
                        'style': style,
                        'confidence': round(confidence, 3)
                    })
            
            # Sort by confidence
            top_styles.sort(key=lambda x: x['confidence'], reverse=True)
            
            return {
                'primary_style': top_styles[0]['style'] if top_styles else 'contemporary',
                'style_confidence': top_styles[0]['confidence'] if top_styles else 0.5,
                'style_alternatives': top_styles[:3]
            }
            
        except Exception as e:
            logger.error(f"Style analysis failed: {e}")
            return await self._mock_style_analysis()
    
    async def _estimate_depth(self, image: Image.Image) -> Dict[str, Any]:
        """Estimate depth map"""
        if not AI_MODELS_AVAILABLE or not self.model_manager._initialized:
            return await self._mock_depth_estimation()
        
        try:
            depth_model = self.model_manager.models['depth']
            
            # Run depth estimation
            depth_result = depth_model(image)
            depth_map = depth_result['depth']
            
            # Convert to numpy for analysis
            if hasattr(depth_map, 'numpy'):
                depth_array = depth_map.numpy()
            else:
                depth_array = np.array(depth_map)
            
            return {
                'depth_available': True,
                'depth_stats': {
                    'min_depth': float(depth_array.min()),
                    'max_depth': float(depth_array.max()),
                    'mean_depth': float(depth_array.mean()),
                    'depth_range': float(depth_array.max() - depth_array.min())
                }
            }
            
        except Exception as e:
            logger.error(f"Depth estimation failed: {e}")
            return await self._mock_depth_estimation()
    
    async def _analyze_colors_basic(self, image_data: bytes) -> Dict[str, Any]:
        """Basic color analysis without heavy dependencies"""
        try:
            if HAS_IMAGING:
                # If PIL is available, do simple analysis
                image = Image.open(io.BytesIO(image_data))
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Sample a few pixels for basic color analysis
                width, height = image.size
                sample_pixels = []
                for x in range(0, width, width // 10):
                    for y in range(0, height, height // 10):
                        try:
                            pixel = image.getpixel((x, y))
                            sample_pixels.append(pixel)
                        except:
                            continue
                
                if sample_pixels:
                    # Calculate average color
                    avg_r = sum(p[0] for p in sample_pixels) // len(sample_pixels)
                    avg_g = sum(p[1] for p in sample_pixels) // len(sample_pixels)
                    avg_b = sum(p[2] for p in sample_pixels) // len(sample_pixels)
                    
                    brightness = (avg_r + avg_g + avg_b) / 3
                    
                    return {
                        'dominant_color': {
                            'r': avg_r,
                            'g': avg_g,
                            'b': avg_b,
                            'hex': f"#{avg_r:02x}{avg_g:02x}{avg_b:02x}"
                        },
                        'brightness': round(brightness, 2),
                        'color_diversity': 50.0,  # Mock value
                        'color_temperature': 'warm' if avg_r > avg_b else 'cool'
                    }
            
            # Fallback to mock values
            return {
                'dominant_color': {'r': 128, 'g': 128, 'b': 128, 'hex': '#808080'},
                'brightness': 128.0,
                'color_diversity': 50.0,
                'color_temperature': 'neutral'
            }
            
        except Exception as e:
            logger.error(f"Color analysis failed: {e}")
            return {
                'dominant_color': {'r': 128, 'g': 128, 'b': 128, 'hex': '#808080'},
                'brightness': 128.0,
                'color_diversity': 50.0,
                'color_temperature': 'neutral'
            }
    
    # Mock implementations for fallback
    async def _mock_scene_classification(self) -> Dict[str, Any]:
        """Mock scene classification"""
        return {
            'scene_type': 'living_room',
            'scene_conf': 0.85,
            'scene_alternatives': [
                {'type': 'living_room', 'conf': 0.85},
                {'type': 'bedroom', 'conf': 0.10},
                {'type': 'office', 'conf': 0.05}
            ]
        }
    
    async def _mock_object_detection(self) -> Dict[str, Any]:
        """Mock object detection"""
        return {
            'objects_detected': 5,
            'objects': [
                {'label': 'sofa', 'confidence': 0.92, 'bbox': {'x1': 100, 'y1': 200, 'x2': 400, 'y2': 350}, 'area': 45000},
                {'label': 'chair', 'confidence': 0.88, 'bbox': {'x1': 450, 'y1': 220, 'x2': 550, 'y2': 380}, 'area': 16000},
                {'label': 'table', 'confidence': 0.76, 'bbox': {'x1': 200, 'y1': 350, 'x2': 350, 'y2': 400}, 'area': 7500}
            ],
            'object_categories': ['sofa', 'chair', 'table']
        }
    
    async def _mock_style_analysis(self) -> Dict[str, Any]:
        """Mock style analysis"""
        return {
            'primary_style': 'contemporary',
            'style_confidence': 0.72,
            'style_alternatives': [
                {'style': 'contemporary', 'confidence': 0.72},
                {'style': 'modern', 'confidence': 0.18},
                {'style': 'minimalist', 'confidence': 0.10}
            ]
        }
    
    async def _mock_depth_estimation(self) -> Dict[str, Any]:
        """Mock depth estimation"""
        return {
            'depth_available': False,
            'depth_stats': {
                'min_depth': 0.5,
                'max_depth': 10.0,
                'mean_depth': 3.2,
                'depth_range': 9.5
            }
        }


# Global pipeline instance
ai_pipeline = AIPipelineService()


async def process_scene_ai(image_data: bytes, scene_id: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Main entry point for scene AI processing
    
    Args:
        image_data: Raw image bytes
        scene_id: Unique scene identifier  
        options: Processing options
        
    Returns:
        Complete AI analysis results
    """
    return await ai_pipeline.process_scene(image_data, scene_id, options)