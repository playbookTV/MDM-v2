"""
Scenes service using Supabase client
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from app.core.supabase import get_supabase
from app.schemas.database import Scene, SceneObject, SceneWithDetails, ObjectWithDetails
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

class SceneService:
    """Service for scene operations"""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.storage = StorageService()
    
    async def get_scenes(
        self, 
        page: int = 1, 
        per_page: int = 20,
        dataset_id: Optional[str] = None,
        review_status: Optional[str] = None,
        scene_type: Optional[str] = None,
        include_objects: bool = False
    ) -> Dict[str, Any]:
        """Get paginated list of scenes"""
        try:
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Build base query
            if include_objects:
                # This would need a proper join in a complex query - for now, we'll fetch separately
                query = self.supabase.table("scenes").select("*")
            else:
                query = self.supabase.table("scenes").select("*")
            
            count_query = self.supabase.table("scenes").select("*", count="exact")
            
            # Apply filters
            if dataset_id:
                query = query.eq("dataset_id", dataset_id)
                count_query = count_query.eq("dataset_id", dataset_id)
            if scene_type:
                query = query.eq("scene_type", scene_type)
                count_query = count_query.eq("scene_type", scene_type)
            # Note: review_status is not in the schema - using status instead
            if review_status and review_status != "all":
                query = query.eq("status", review_status)
                count_query = count_query.eq("status", review_status)
            
            # Get total count
            total_count = count_query.execute().count
            
            # Get paginated data
            result = query.range(offset, offset + per_page - 1).order("created_at", desc=True).execute()
            
            # If including objects, fetch them separately for now
            scenes_with_details = []
            for scene_data in result.data:
                scene = Scene(**scene_data)
                
                if include_objects:
                    # Get objects for this scene
                    objects_result = (
                        self.supabase.table("objects")
                        .select("*")
                        .eq("scene_id", scene.id)
                        .execute()
                    )
                    objects = [SceneObject(**obj) for obj in objects_result.data]
                    
                    # Create enhanced scene with objects
                    scene_dict = scene.model_dump()
                    scene_dict["objects"] = objects
                    scenes_with_details.append(scene_dict)
                else:
                    scenes_with_details.append(scene.model_dump())
            
            return {
                "data": scenes_with_details,
                "count": len(scenes_with_details),
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": (total_count + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Failed to get scenes: {e}")
            raise
    
    async def get_scene(self, scene_id: str, include_objects: bool = True) -> Optional[Dict[str, Any]]:
        """Get scene by ID with optional objects"""
        try:
            # Get scene
            result = self.supabase.table("scenes").select("*").eq("id", scene_id).execute()
            
            if not result.data:
                return None
            
            scene_data = result.data[0]
            scene = Scene(**scene_data)
            
            # Get dataset name
            if scene.dataset_id:
                dataset_result = (
                    self.supabase.table("datasets")
                    .select("name")
                    .eq("id", scene.dataset_id)
                    .execute()
                )
                if dataset_result.data:
                    scene_data["dataset_name"] = dataset_result.data[0]["name"]
            
            # Get objects if requested
            if include_objects:
                objects_result = (
                    self.supabase.table("objects")
                    .select("*")
                    .eq("scene_id", scene_id)
                    .execute()
                )
                objects = [SceneObject(**obj) for obj in objects_result.data]
                scene_data["objects"] = [obj.model_dump() for obj in objects]
            
            return scene_data
            
        except Exception as e:
            logger.error(f"Failed to get scene {scene_id}: {e}")
            raise
    
    async def get_scene_objects(self, scene_id: str) -> List[SceneObject]:
        """Get all objects detected in a scene"""
        try:
            result = (
                self.supabase.table("objects")
                .select("*")
                .eq("scene_id", scene_id)
                .execute()
            )
            
            return [SceneObject(**obj) for obj in result.data]
            
        except Exception as e:
            logger.error(f"Failed to get objects for scene {scene_id}: {e}")
            raise
    
    async def get_scene_image_url(
        self, 
        scene_id: str, 
        image_type: str = "original"
    ) -> Optional[str]:
        """Get public URL for viewing scene images"""
        try:
            # Get scene to find the R2 key
            result = self.supabase.table("scenes").select("*").eq("id", scene_id).execute()
            
            if not result.data:
                return None
            
            scene = Scene(**result.data[0])
            
            # Get appropriate R2 key
            r2_key = None
            if image_type == "original":
                r2_key = scene.r2_key_original
            elif image_type == "depth":
                r2_key = scene.depth_key
            # Note: thumbnail is not in the schema, would need to be added
            
            if not r2_key:
                return None
            
            # Use public URL instead of presigned URL since the bucket is public
            url = self.storage.get_public_url(r2_key)
            return url
            
        except Exception as e:
            logger.error(f"Failed to get image URL for scene {scene_id}: {e}")
            raise
    
    async def update_scene(self, scene_id: str, updates: Dict[str, Any]) -> bool:
        """Update scene metadata (for corrections/reviews)"""
        try:
            # Filter allowed updates
            allowed_fields = [
                'scene_type', 'scene_conf', 'status', 'depth_key'
            ]
            
            filtered_updates = {
                k: v for k, v in updates.items() 
                if k in allowed_fields
            }
            
            if not filtered_updates:
                return False
            
            result = (
                self.supabase.table("scenes")
                .update(filtered_updates)
                .eq("id", scene_id)
                .execute()
            )
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to update scene {scene_id}: {e}")
            raise
    
    async def update_scene_object(
        self, 
        scene_id: str, 
        object_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update scene object metadata"""
        try:
            # Verify object belongs to scene
            result = (
                self.supabase.table("objects")
                .select("id")
                .eq("id", object_id)
                .eq("scene_id", scene_id)
                .execute()
            )
            
            if not result.data:
                return False
            
            # Filter allowed updates
            allowed_fields = [
                'category_code', 'subcategory', 'confidence', 'description'
            ]
            
            filtered_updates = {
                k: v for k, v in updates.items() 
                if k in allowed_fields
            }
            
            if not filtered_updates:
                return False
            
            update_result = (
                self.supabase.table("objects")
                .update(filtered_updates)
                .eq("id", object_id)
                .execute()
            )
            
            return len(update_result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to update object {object_id} in scene {scene_id}: {e}")
            raise
    
    # Pagination utility for frontend compatibility
    async def get_scenes_paginated(
        self,
        dataset_id: Optional[str] = None,
        review_status: Optional[str] = None,
        scene_type: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get scenes with pagination info formatted for React hooks"""
        result = await self.get_scenes(
            page=1,
            per_page=limit,
            dataset_id=dataset_id,
            review_status=review_status,
            scene_type=scene_type,
            include_objects=False
        )
        
        return {
            "scenes": result["data"],
            "isLoading": False,
            "error": None,
            "getNextScene": None,  # Would implement with proper pagination
            "getPreviousScene": None,  # Would implement with proper pagination
            "getSceneIndex": None  # Would implement with scene ordering
        }