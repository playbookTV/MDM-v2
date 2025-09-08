"""
Image serving endpoints
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import RedirectResponse

from app.services.scenes import SceneService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/scenes/{scene_id}.jpg")
async def get_scene_image(
    scene_id: str,
    type: str = Query("original", description="Image type: original, thumbnail, depth")
):
    """Serve scene images by redirecting to presigned R2 URLs"""
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
        
        # Redirect to the presigned R2 URL
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
