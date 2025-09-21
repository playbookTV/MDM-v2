"""
RunPod Serverless Client for AI processing
"""

import logging
import json
import uuid
import httpx
import asyncio
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)



def _serialize_uuids(obj):
    """Custom JSON serializer that handles UUID objects"""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, (list, tuple)):
        return [_serialize_uuids(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: _serialize_uuids(value) for key, value in obj.items()}
    else:
        return obj

class RunPodClient:
    """Client for RunPod serverless AI processing"""
    
    def __init__(self):
        self.api_key = settings.RUNPOD_API_KEY
        self.endpoint_id = settings.RUNPOD_ENDPOINT_ID
        self.endpoint_url = settings.RUNPOD_ENDPOINT_URL
        self.timeout = settings.RUNPOD_TIMEOUT
        self.max_retries = settings.RUNPOD_MAX_RETRIES
        
        # RunPod API URLs
        self.base_url = "https://api.runpod.ai/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Track request statistics
        self.stats = {
            "requests_made": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "last_request_time": None
        }
    
    def is_configured(self) -> bool:
        """Check if RunPod is properly configured"""
        return bool(self.api_key and (self.endpoint_id or self.endpoint_url))
    
    async def process_scenes_batch_runpod(
        self,
        scenes_data: List[Dict[str, Any]], 
        batch_size: int = 3,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process multiple scenes using RunPod batch endpoint
        
        Args:
            scenes_data: List of {"scene_id": str, "image_data": bytes} dicts
            batch_size: Number of scenes to process in parallel (1-8)
            options: Processing options
            
        Returns:
            {"status": "success"|"error", "batch_results": List[Dict], "success_rate": float}
        """
        if not self.is_configured():
            logger.warning("RunPod not configured, cannot process batch")
            return {
                "status": "error",
                "error": "RunPod not configured",
                "success": False,
                "batch_results": []
            }
        
        if not scenes_data:
            return {
                "status": "success", 
                "batch_results": [],
                "success_rate": 100.0,
                "success": True
            }
        
        try:
            # Prepare batch images for RunPod handler
            batch_images = []
            for scene_data in scenes_data:
                scene_id = scene_data["scene_id"]
                image_data = scene_data["image_data"]
                
                # Encode image as base64
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                batch_images.append((scene_id, image_b64))
            
            # Prepare batch request payload
            payload = {
                "input": {
                    "batch_images": batch_images,
                    "batch_size": min(batch_size, 8),  # Cap at RunPod handler limit
                    "options": options or {}
                }
            }
            
            # Track batch request
            self.stats["requests_made"] += 1
            self.stats["last_request_time"] = datetime.utcnow()
            
            logger.info(f"🚀 Processing batch of {len(batch_images)} scenes with batch_size={batch_size}")
            
            # Send batch request to RunPod
            result = await self._request_serverless_endpoint(payload)
            
            if result.get("status") == "success":
                self.stats["successful_requests"] += 1
                batch_results = result.get("result", {}).get("batch_results", [])
                
                # Calculate success rate
                successful = sum(1 for r in batch_results if r.get("status") == "success")
                success_rate = (successful / len(batch_results) * 100) if batch_results else 0
                
                logger.info(f"✅ Batch processing completed: {successful}/{len(batch_results)} scenes successful ({success_rate:.1f}%)")
                
                return {
                    "status": "success",
                    "batch_results": batch_results,
                    "success_rate": success_rate,
                    "success": True
                }
            else:
                self.stats["failed_requests"] += 1
                logger.error(f"❌ Batch processing failed: {result.get('error')}")
                return {
                    "status": "error", 
                    "error": result.get("error", "Batch processing failed"),
                    "batch_results": [],
                    "success": False
                }
                
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"RunPod batch client error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "batch_results": [],
                "success": False
            }

    async def process_scene_runpod(
        self, 
        image_data: bytes, 
        scene_id: str,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process scene using RunPod serverless endpoint
        
        Args:
            image_data: Raw image bytes
            scene_id: Unique scene identifier
            options: Processing options
            
        Returns:
            AI processing results
        """
        if not self.is_configured():
            logger.warning("RunPod not configured, cannot process image")
            return {
                "status": "error",
                "error": "RunPod not configured",
                "success": False
            }
        
        try:
            # Encode image as base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare request payload
            payload = {
                "input": {
                    "image": image_b64,
                    "scene_id": scene_id,
                    "options": options or {}
                }
            }
            
            # Track request
            self.stats["requests_made"] += 1
            self.stats["last_request_time"] = datetime.utcnow()
            
            # Always use serverless endpoint (our endpoint is serverless)
            result = await self._request_serverless_endpoint(payload)
            
            if result.get("status") == "success":
                self.stats["successful_requests"] += 1
                logger.info(f"✅ RunPod processing completed for scene {scene_id}")
            else:
                self.stats["failed_requests"] += 1
                logger.error(f"❌ RunPod processing failed for scene {scene_id}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"RunPod client error for scene {scene_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "success": False
            }
    
    async def _request_serverless_endpoint(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to RunPod serverless endpoint"""
        # Use our HTTP endpoint directly
        async with httpx.AsyncClient() as client:
            # Make initial request to our HTTP server
            response = await client.post(
                self.endpoint_url,
                json=_serialize_uuids(payload.get("input", {})),  # Send just the input data, handling UUIDs
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "success": False
                }
            
            result = response.json()
            
            # Handle our HTTP server response format
            if result.get("status") == "success":
                return {
                    "status": "success", 
                    "result": result.get("result", {}),
                    "success": True
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error", "AI processing failed"),
                    "success": False
                }
    
    async def _request_custom_endpoint(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to custom RunPod endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.endpoint_url,
                json=_serialize_uuids(payload),
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "success": False
                }
            
            return response.json()
    
    async def _poll_for_completion(self, job_id: str, max_polls: int = 60) -> Dict[str, Any]:
        """Poll RunPod job until completion"""
        url = f"{self.base_url}/{self.endpoint_id}/status/{job_id}"
        
        async with httpx.AsyncClient() as client:
            for attempt in range(max_polls):
                try:
                    response = await client.get(url, headers=self.headers, timeout=30)
                    
                    if response.status_code != 200:
                        await asyncio.sleep(5)
                        continue
                    
                    result = response.json()
                    status = result.get("status")
                    
                    if status == "COMPLETED":
                        return {
                            "status": "success",
                            "result": result.get("output", {}),
                            "success": True
                        }
                    elif status == "FAILED":
                        return {
                            "status": "error",
                            "error": result.get("error", "RunPod job failed"),
                            "success": False
                        }
                    elif status in ["IN_QUEUE", "IN_PROGRESS"]:
                        # Continue polling
                        await asyncio.sleep(5)
                        continue
                    else:
                        return {
                            "status": "error",
                            "error": f"Unknown status: {status}",
                            "success": False
                        }
                        
                except Exception as e:
                    logger.warning(f"Polling attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(5)
            
            return {
                "status": "error", 
                "error": "RunPod job timed out",
                "success": False
            }
    
    async def process_scene(
        self, 
        image_data: str, 
        scene_id: str,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process scene using RunPod serverless endpoint (base64 image)
        
        Args:
            image_data: Base64 encoded image string
            scene_id: Unique scene identifier
            options: Processing options
            
        Returns:
            AI processing results with success flag
        """
        if not self.is_configured():
            logger.warning("RunPod not configured, cannot process image")
            return {
                "success": False,
                "error": "RunPod not configured"
            }
        
        try:
            # Prepare request payload
            payload = {
                "input": {
                    "image": image_data,
                    "scene_id": scene_id,
                    "options": options or {}
                }
            }
            
            # Track request
            self.stats["requests_made"] += 1
            self.stats["last_request_time"] = datetime.utcnow()
            
            # Always use serverless endpoint (our endpoint is serverless)
            result = await self._request_serverless_endpoint(payload)
            
            if result.get("status") == "success":
                self.stats["successful_requests"] += 1
                logger.info(f"✅ RunPod processing completed for scene {scene_id}")
                return {
                    "success": True,
                    "response": result.get("result", result)
                }
            else:
                self.stats["failed_requests"] += 1
                logger.error(f"❌ RunPod processing failed for scene {scene_id}: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Unknown RunPod error")
                }
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"RunPod client error for scene {scene_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def health_check(self) -> Dict[str, Any]:
        """Check RunPod endpoint health"""
        if not self.is_configured():
            return {
                "success": False,
                "error": "RunPod not configured"
            }
        
        try:
            # Use direct HTTP endpoint health check
            health_url = self.endpoint_url.replace('/process', '/health')
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    health_url,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Direct HTTP endpoint returns simple health status
                    if result.get("status") == "healthy":
                        return {
                            "success": True,
                            "response": result
                        }
                
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        success_rate = 0
        if self.stats["requests_made"] > 0:
            success_rate = (self.stats["successful_requests"] / self.stats["requests_made"]) * 100
        
        return {
            "requests_made": self.stats["requests_made"],
            "successful_requests": self.stats["successful_requests"], 
            "failed_requests": self.stats["failed_requests"],
            "success_rate_percent": round(success_rate, 1),
            "last_request_time": self.stats["last_request_time"].isoformat() if self.stats["last_request_time"] else None,
            "configured": self.is_configured()
        }
    
    async def get_endpoint_info(self) -> Dict[str, Any]:
        """Get RunPod endpoint information"""
        if not self.is_configured():
            return {"error": "RunPod not configured"}
        
        try:
            url = f"{self.base_url}/{self.endpoint_id}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            return {"error": str(e)}


# Global RunPod client instance
runpod_client = RunPodClient()


async def process_scene_with_runpod(
    image_data: bytes,
    scene_id: str, 
    options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Main entry point for RunPod scene processing
    
    Args:
        image_data: Raw image bytes
        scene_id: Unique scene identifier
        options: Processing options
        
    Returns:
        AI processing results
    """
    return await runpod_client.process_scene_runpod(image_data, scene_id, options)
