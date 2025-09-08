"""
Reviews service using Supabase client
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from app.core.supabase import get_supabase
from app.schemas.database import Review, ReviewCreate

logger = logging.getLogger(__name__)

class ReviewService:
    """Service for review operations"""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    async def create_review(self, review_data: ReviewCreate) -> Review:
        """Create a new review/annotation"""
        try:
            # Convert to dict and add ID
            data = review_data.model_dump()
            data["id"] = str(uuid4())
            
            # Convert UUID fields to strings for database insertion
            if "target_id" in data and isinstance(data["target_id"], UUID):
                data["target_id"] = str(data["target_id"])
            
            result = self.supabase.table("reviews").insert(data).execute()
            
            # Convert result back to Review, handling UUID conversion
            review_data_dict = result.data[0]
            
            # Convert string UUIDs back to UUID objects for the response model
            if "id" in review_data_dict:
                review_data_dict["id"] = UUID(review_data_dict["id"])
            if "target_id" in review_data_dict:
                review_data_dict["target_id"] = UUID(review_data_dict["target_id"])
                
            return Review(**review_data_dict)
            
        except Exception as e:
            logger.error(f"Failed to create review: {e}")
            raise
    
    async def create_batch_reviews(self, reviews_data: List[Dict[str, Any]]) -> List[str]:
        """Create multiple reviews in a batch"""
        try:
            review_records = []
            
            for review_data in reviews_data:
                scene_id = review_data.get("scene_id")
                status = review_data.get("status", "approve")
                notes = review_data.get("notes")
                
                if not scene_id:
                    continue
                
                # Map status to verdict
                verdict_map = {
                    "approved": "approve",
                    "rejected": "reject", 
                    "corrected": "edit"
                }
                verdict = verdict_map.get(status, "approve")
                
                record = {
                    "id": str(uuid4()),
                    "target": "scene",
                    "target_id": scene_id,
                    "verdict": verdict,
                    "notes": notes,
                    "reviewer_id": "anonymous"  # TODO: Get from auth context
                }
                
                review_records.append(record)
            
            if not review_records:
                return []
            
            result = self.supabase.table("reviews").insert(review_records).execute()
            
            return [review["id"] for review in result.data]
            
        except Exception as e:
            logger.error(f"Failed to create batch reviews: {e}")
            raise
    
    async def get_review_progress(self, dataset_id: Optional[str] = None) -> Dict[str, Any]:
        """Get review progress statistics"""
        try:
            # Base query for scenes
            query = self.supabase.table("scenes").select("id, status")
            
            if dataset_id:
                query = query.eq("dataset_id", dataset_id)
            
            result = query.execute()
            
            # Count by status (using 'status' field from scenes table)
            total = len(result.data)
            status_counts = {}
            
            for scene in result.data:
                status = scene.get("status", "pending")
                # Map database statuses to review statuses
                if status == "processed":
                    status = "pending"  # Default for processed scenes
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Calculate metrics
            pending = status_counts.get("pending", total)  # Default to all pending
            approved = status_counts.get("approved", 0)
            rejected = status_counts.get("rejected", 0)
            corrected = status_counts.get("corrected", 0)
            
            reviewed = approved + rejected + corrected
            completion_rate = (reviewed / total * 100) if total > 0 else 0
            
            return {
                "total_scenes": total,
                "pending_scenes": pending,
                "approved_scenes": approved,
                "rejected_scenes": rejected,
                "corrected_scenes": corrected,
                "completion_rate": completion_rate
            }
            
        except Exception as e:
            logger.error(f"Failed to get review progress: {e}")
            raise
    
    async def start_review_session(self, dataset_id: Optional[str] = None) -> Dict[str, Any]:
        """Start a new review session (mock implementation)"""
        try:
            # In a full implementation, this would create a session record
            session = {
                "id": str(uuid4()),
                "dataset_id": dataset_id,
                "name": "Review Session",
                "reviewer": "anonymous",
                "scenes_reviewed": 0,
                "started_at": datetime.utcnow(),
                "ended_at": None
            }
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to start review session: {e}")
            raise
    
    async def end_review_session(self, session_id: str) -> Dict[str, Any]:
        """End a review session (mock implementation)"""
        try:
            # In a full implementation, this would update the session record
            session = {
                "id": session_id,
                "dataset_id": None,
                "name": "Review Session",
                "reviewer": "anonymous",
                "scenes_reviewed": 0,  # Would calculate from actual reviews
                "started_at": datetime.utcnow(),  # Would get from session record
                "ended_at": datetime.utcnow()
            }
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to end review session {session_id}: {e}")
            raise
    
    async def apply_scene_corrections(self, scene_id: str, corrections: Dict[str, Any]) -> bool:
        """Apply corrections to a scene"""
        try:
            # Filter corrections to allowed fields
            allowed_fields = ["scene_type", "scene_conf"]
            scene_updates = {
                k: v for k, v in corrections.items() 
                if k in allowed_fields
            }
            
            if not scene_updates:
                return False
            
            # Update the scene
            result = (
                self.supabase.table("scenes")
                .update(scene_updates)
                .eq("id", scene_id)
                .execute()
            )
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to apply scene corrections: {e}")
            raise
    
    async def apply_object_corrections(self, object_id: str, corrections: Dict[str, Any]) -> bool:
        """Apply corrections to an object"""
        try:
            # Filter corrections to allowed fields
            allowed_fields = ["category_code", "subcategory", "confidence"]
            object_updates = {
                k: v for k, v in corrections.items() 
                if k in allowed_fields
            }
            
            if not object_updates:
                return False
            
            # Update the object
            result = (
                self.supabase.table("objects")
                .update(object_updates)
                .eq("id", object_id)
                .execute()
            )
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to apply object corrections: {e}")
            raise