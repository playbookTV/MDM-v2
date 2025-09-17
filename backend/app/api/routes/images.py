"""
Image serving endpoints
"""

import logging
from typing import Optional
import httpx

from fastapi import APIRouter, HTTPException, Query, Response, Request
from fastapi.responses import RedirectResponse, StreamingResponse

from app.services.scenes import SceneService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/scenes/{scene_id}.jpg")
async def get_scene_image(
    scene_id: str,
    request: Request,
    type: str = Query("original", description="Image type: original, thumbnail, depth")
):
    """
    Serve scene images - either proxy or redirect based on client needs.
    Canvas rendering requires proxy mode to avoid CORS issues.
    """
    try:
        service = SceneService()
        
        # Map frontend types to backend types
        image_type_mapping = {
            "original": "original",
            "thumbnail": "thumbnail",
            "depth": "depth"
        }
        
        backend_type = image_type_mapping.get(type, "original")
        
        # Get presigned URL
        url = await service.get_scene_image_url(scene_id, backend_type)
        
        if not url:
            if backend_type == "original":
                raise HTTPException(status_code=404, detail="Scene image not found")
            else:
                raise HTTPException(status_code=404, detail=f"No {type} image available")
        
        # Check if request needs proxy (for Canvas/CORS support)
        user_agent = request.headers.get("user-agent", "").lower()
        needs_proxy = (
            "canvas" in user_agent or 
            request.headers.get("x-canvas-mode") == "true" or
            request.query_params.get("proxy") == "true"
        )
        
        if needs_proxy:
            # Proxy the image through the backend to handle CORS
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Failed to fetch image from storage"
                    )
                
                return Response(
                    content=response.content,
                    media_type=response.headers.get("content-type", "image/jpeg"),
                    headers={
                        "Cache-Control": "public, max-age=3600",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type",
                    }
                )
        else:
            # Regular redirect for DOM-based rendering
            return RedirectResponse(url=url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve image for scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve image")

@router.get("/scenes/{scene_id}/thumbnail")
async def get_scene_thumbnail(scene_id: str):
    """Alternative endpoint for thumbnails"""
    return await get_scene_image(scene_id, type="thumbnail")
