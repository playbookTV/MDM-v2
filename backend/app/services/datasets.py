"""
Dataset service using Supabase client
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from app.core.supabase import get_supabase
from app.schemas.database import Dataset, DatasetCreate, Scene
from app.schemas.dataset import SceneCreate

logger = logging.getLogger(__name__)

class DatasetService:
    """Service for dataset operations"""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    async def get_datasets(
        self, 
        page: int = 1, 
        per_page: int = 20,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get paginated list of datasets"""
        try:
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Build query
            query = self.supabase.table("datasets").select("*")
            
            if search:
                query = query.ilike("name", f"%{search}%")
            
            # Get total count
            count_result = self.supabase.table("datasets").select("*", count="exact")
            if search:
                count_result = count_result.ilike("name", f"%{search}%")
            total_count = count_result.execute().count
            
            # Get paginated data
            result = query.range(offset, offset + per_page - 1).order("created_at", desc=True).execute()
            
            return {
                "data": result.data,
                "count": len(result.data),
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": (total_count + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Failed to get datasets: {e}")
            raise
    
    async def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """Get dataset by ID"""
        try:
            result = self.supabase.table("datasets").select("*").eq("id", dataset_id).execute()
            
            if result.data:
                return Dataset(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get dataset {dataset_id}: {e}")
            raise
    
    async def create_dataset(self, dataset_data: DatasetCreate) -> Dataset:
        """Create a new dataset"""
        try:
            # Convert to dict and add ID
            data = dataset_data.model_dump()
            data["id"] = str(uuid4())
            
            result = self.supabase.table("datasets").insert(data).execute()
            
            return Dataset(**result.data[0])
            
        except Exception as e:
            logger.error(f"Failed to create dataset: {e}")
            raise
    
    async def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset"""
        try:
            result = self.supabase.table("datasets").delete().eq("id", dataset_id).execute()
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to delete dataset {dataset_id}: {e}")
            raise
    
    async def get_dataset_scenes(
        self, 
        dataset_id: str,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """Get scenes for a dataset"""
        try:
            offset = (page - 1) * per_page
            
            # Get total count
            count_result = self.supabase.table("scenes").select("*", count="exact").eq("dataset_id", dataset_id)
            total_count = count_result.execute().count
            
            # Get paginated scenes
            result = (
                self.supabase.table("scenes")
                .select("*")
                .eq("dataset_id", dataset_id)
                .range(offset, offset + per_page - 1)
                .order("created_at", desc=True)
                .execute()
            )
            
            return {
                "data": result.data,
                "count": len(result.data),
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": (total_count + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Failed to get scenes for dataset {dataset_id}: {e}")
            raise
    
    async def create_scene(self, scene_data: SceneCreate) -> Scene:
        """Create a scene in a dataset"""
        try:
            data = scene_data.model_dump()
            data["id"] = str(uuid4())
            
            result = self.supabase.table("scenes").insert(data).execute()
            
            return Scene(**result.data[0])
            
        except Exception as e:
            logger.error(f"Failed to create scene: {e}")
            raise
    
    async def create_scenes_batch(self, scenes_data: List[SceneCreate]) -> List[Scene]:
        """Create multiple scenes in batch"""
        try:
            data_list = []
            for scene_data in scenes_data:
                data = scene_data.model_dump()
                data["id"] = str(uuid4())
                data_list.append(data)
            
            result = self.supabase.table("scenes").insert(data_list).execute()
            
            return [Scene(**scene) for scene in result.data]
            
        except Exception as e:
            logger.error(f"Failed to create scenes batch: {e}")
            raise
    
    def get_dataset_sync(self, dataset_id: str) -> Optional[Dataset]:
        """Sync version for Celery tasks - get dataset by ID"""
        try:
            result = self.supabase.table("datasets").select("*").eq("id", dataset_id).execute()
            
            if result.data:
                return Dataset(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get dataset {dataset_id}: {e}")
            raise
    
    def create_scene_sync(self, dataset_id: str, scene_data: SceneCreate) -> Scene:
        """Sync version for Celery tasks - create a scene in a dataset"""
        try:
            data = scene_data.model_dump()
            data["id"] = str(uuid4())
            data["dataset_id"] = dataset_id
            
            result = self.supabase.table("scenes").insert(data).execute()
            
            return Scene(**result.data[0])
            
        except Exception as e:
            logger.error(f"Failed to create scene: {e}")
            raise