"""
Scenes service using Supabase client
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from app.core.supabase import get_supabase
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

class SceneService:
    """Service for scene operations"""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.storage = StorageService()
    
    def _transform_object_data(self, obj_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform database object format to schema format"""
        # Convert Supabase object format to proper bbox format for frontend
        transformed = obj_data.copy()
        
        # Convert separate bbox columns to bbox object if they exist
        if ("bbox_x" in obj_data and "bbox_y" in obj_data and 
            "bbox_w" in obj_data and "bbox_h" in obj_data):
            transformed["bbox"] = {
                "x": float(obj_data["bbox_x"]),
                "y": float(obj_data["bbox_y"]),
                "width": float(obj_data["bbox_w"]),
                "height": float(obj_data["bbox_h"])
            }
        
        # Map category_code to label for frontend compatibility
        if "category_code" in obj_data and "label" not in obj_data:
            transformed["label"] = obj_data["category_code"] or "object"
        
        return transformed
    
    def _enrich_scene_data(self, scene_data: Dict[str, Any], objects: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Add computed fields to scene data for frontend compatibility"""
        enriched = scene_data.copy()
        
        # Add has_depth computed field (support legacy and new columns)
        enriched["has_depth"] = bool(scene_data.get("r2_key_depth") or scene_data.get("depth_key"))
        
        # Add objects_count computed field
        if objects is not None:
            enriched["objects_count"] = len(objects)
        elif "objects" in scene_data:
            enriched["objects_count"] = len(scene_data["objects"])
        else:
            # Will be computed separately for bulk queries
            enriched["objects_count"] = 0
        
        # Map status to review_status for frontend compatibility
        status = scene_data.get("status", "unprocessed")
        if status == "processed":
            enriched["review_status"] = "approved"  # Default processed scenes to approved
        elif status == "failed":
            enriched["review_status"] = "rejected"
        else:
            enriched["review_status"] = "pending"
        
        return enriched
    
    async def _get_objects_count_bulk(self, scene_ids: List[str]) -> Dict[str, int]:
        """Get object counts for multiple scenes efficiently"""
        try:
            # Get counts for all scenes in one query
            result = (
                self.supabase.table("objects")
                .select("scene_id")
                .in_("scene_id", scene_ids)
                .execute()
            )
            
            # Count objects per scene
            counts = {}
            for obj in result.data:
                scene_id = obj["scene_id"]
                counts[scene_id] = counts.get(scene_id, 0) + 1
            
            # Ensure all scene IDs have a count (even if 0)
            for scene_id in scene_ids:
                if scene_id not in counts:
                    counts[scene_id] = 0
            
            return counts
            
        except Exception as e:
            logger.error(f"Failed to get bulk object counts: {e}")
            # Return zeros for all scenes as fallback
            return {scene_id: 0 for scene_id in scene_ids}
    
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
            
            # Process scenes and add computed fields
            scenes_with_details = []
            scene_ids = [scene_data["id"] for scene_data in result.data]
            
            # Get object counts for all scenes in one query (more efficient)
            if not include_objects:
                object_counts = await self._get_objects_count_bulk(scene_ids)
            
            for scene_data in result.data:
                scene_dict = dict(scene_data)
                
                if include_objects:
                    # Get objects for this scene
                    objects_result = (
                        self.supabase.table("objects")
                        .select("*")
                        .eq("scene_id", scene_data["id"])
                        .execute()
                    )
                    objects = [self._transform_object_data(obj) for obj in objects_result.data]
                    scene_dict["objects"] = objects
                    
                    # Enrich with computed fields (including object count)
                    enriched_scene = self._enrich_scene_data(scene_dict, objects)
                else:
                    # Use bulk object count
                    scene_dict["objects_count"] = object_counts.get(str(scene.id), 0)
                    
                    # Enrich with computed fields
                    enriched_scene = self._enrich_scene_data(scene_dict)
                
                scenes_with_details.append(enriched_scene)
            
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
            
            scene_data = dict(result.data[0])
            
            # Get dataset name
            if scene_data.get("dataset_id"):
                dataset_result = (
                    self.supabase.table("datasets")
                    .select("name")
                    .eq("id", scene_data.get("dataset_id"))
                    .execute()
                )
                if dataset_result.data:
                    scene_data["dataset_name"] = dataset_result.data[0]["name"]
            
            # Get objects if requested
            objects = None
            if include_objects:
                objects_result = (
                    self.supabase.table("objects")
                    .select("*")
                    .eq("scene_id", scene_id)
                    .execute()
                )
                
                # Return raw objects (frontend normalizes bbox)
                objects = [self._transform_object_data(obj) for obj in objects_result.data]
                scene_data["objects"] = objects
            else:
                # Get object count for this scene
                objects_count_result = (
                    self.supabase.table("objects")
                    .select("*", count="exact")
                    .eq("scene_id", scene_id)
                    .execute()
                )
                scene_data["objects_count"] = objects_count_result.count or 0
            
            # Enrich with computed fields
            enriched_scene = self._enrich_scene_data(scene_data, objects)
            
            return enriched_scene
            
        except Exception as e:
            logger.error(f"Failed to get scene {scene_id}: {e}")
            raise
    
    async def get_scene_objects(self, scene_id: str) -> List[Dict[str, Any]]:
        """Get all objects detected in a scene"""
        try:
            result = (
                self.supabase.table("objects")
                .select("*")
                .eq("scene_id", scene_id)
                .execute()
            )
            
            # Transform database format to schema format (return dicts)
            return [self._transform_object_data(obj_data) for obj_data in result.data]
            
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
            
            scene_row = dict(result.data[0])
            
            # Get appropriate R2 key
            r2_key = None
            if image_type == "original":
                r2_key = scene_row.get("r2_key_original")
            elif image_type == "thumbnail":
                # Prefer explicit thumbnail key; fallback to original to avoid 404s in UI
                r2_key = scene_row.get("r2_key_thumbnail") or scene_row.get("r2_key_original")
            elif image_type == "depth":
                # Support both legacy 'depth_key' and new 'r2_key_depth'
                r2_key = scene_row.get("r2_key_depth") or scene_row.get("depth_key")
            
            if not r2_key:
                return None
            
            # Use public URL instead of presigned URL since the bucket is public
            url = self.storage.get_public_url(r2_key)
            return url
            
        except Exception as e:
            logger.error(f"Failed to get image URL for scene {scene_id}: {e}")
            raise
    
    async def update_scene(self, scene_id: str, updates: Dict[str, Any]) -> bool:
        """Update scene metadata (for corrections/reviews and AI outputs)"""
        try:
            # Normalize incoming keys for Supabase schema compatibility
            normalized = dict(updates)
            # Map r2_key_depth -> depth_key if depth_key not provided
            if 'r2_key_depth' in normalized and 'depth_key' not in normalized:
                normalized['depth_key'] = normalized['r2_key_depth']
            
            # Allowed fields in Supabase scenes table
            allowed_fields = [
                'scene_type', 'scene_conf', 'status', 'depth_key',
                'r2_key_thumbnail', 'palette', 'phash'
            ]
            
            filtered_updates = {k: v for k, v in normalized.items() if k in allowed_fields}
            
            if not filtered_updates:
                logger.info(f"No allowed scene updates for {scene_id}; received keys: {list(updates.keys())}")
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
