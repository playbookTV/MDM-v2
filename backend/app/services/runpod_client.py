"""
RunPod Serverless Client for AI processing
"""

import logging
import httpx
import asyncio
import base64
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


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
                json=payload.get("input", {}),  # Send just the input data
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
                json=payload,
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