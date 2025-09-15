"""
Reviews service using Supabase client
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import HTTPException

from app.core.supabase import get_supabase
from app.schemas.database import Review, ReviewCreate

logger = logging.getLogger(__name__)

class ReviewService:
    """Service for review operations"""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    async def create_review(self, review_data: ReviewCreate, session_id: Optional[str] = None, review_time_seconds: Optional[int] = None) -> Review:
        """Create a new review/annotation"""
        try:
            # Convert to dict and add ID
            data = review_data.model_dump()
            data["id"] = str(uuid4())
            
            # Add session and timing data if provided
            if session_id:
                data["session_id"] = session_id
            if review_time_seconds:
                data["review_time_seconds"] = review_time_seconds
            
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
            logger.error(f"Failed to create review: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to create review")
    
    async def create_batch_reviews(self, reviews_data: List[Dict[str, Any]], session_id: Optional[str] = None) -> List[str]:
        """Create multiple reviews in a batch"""
        try:
            review_records = []
            
            for review_data in reviews_data:
                scene_id = review_data.get("scene_id")
                status = review_data.get("status", "approve")
                notes = review_data.get("notes")
                review_time = review_data.get("review_time_seconds")
                
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
                
                # Add session and timing data if available
                if session_id:
                    record["session_id"] = session_id
                if review_time:
                    record["review_time_seconds"] = review_time
                
                review_records.append(record)
            
            if not review_records:
                logger.warning("No valid review records to create")
                return []
            
            result = self.supabase.table("reviews").insert(review_records).execute()
            
            if not result.data:
                raise Exception("Database insert returned no data")
            
            return [review["id"] for review in result.data]
            
        except Exception as e:
            logger.error(f"Failed to create batch reviews: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to create batch reviews")
    
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
            logger.error(f"Failed to get review progress: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to get review progress")
    
    async def start_review_session(self, dataset_id: Optional[str] = None, reviewer_id: str = "anonymous") -> Dict[str, Any]:
        """Start a new review session and persist to database"""
        try:
            session_data = {
                "id": str(uuid4()),
                "dataset_id": dataset_id,
                "name": "Review Session",
                "reviewer_id": reviewer_id,
                "started_at": datetime.utcnow().isoformat(),
                "scenes_count": 0
            }
            
            # Insert session into database
            result = self.supabase.table("review_sessions").insert(session_data).execute()
            
            if not result.data:
                raise Exception("Failed to create session record")
            
            session = result.data[0]
            
            # Convert to expected format
            return {
                "id": session["id"],
                "dataset_id": session["dataset_id"],
                "name": session["name"],
                "reviewer": session["reviewer_id"],
                "scenes_reviewed": session["scenes_count"],
                "started_at": datetime.fromisoformat(session["started_at"].replace('Z', '+00:00')),
                "ended_at": None
            }
            
        except Exception as e:
            logger.error(f"Failed to start review session: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to start review session")
    
    async def end_review_session(self, session_id: str) -> Dict[str, Any]:
        """End a review session and calculate final stats"""
        try:
            # Get current session
            session_result = (
                self.supabase.table("review_sessions")
                .select("*")
                .eq("id", session_id)
                .execute()
            )
            
            if not session_result.data:
                raise HTTPException(status_code=404, detail="Session not found")
            
            session = session_result.data[0]
            
            # Count reviews created in this session
            reviews_result = (
                self.supabase.table("reviews")
                .select("id")
                .eq("session_id", session_id)
                .execute()
            )
            
            scenes_reviewed = len(reviews_result.data)
            ended_at = datetime.utcnow().isoformat()
            
            # Update session with end time and final count
            update_result = (
                self.supabase.table("review_sessions")
                .update({
                    "ended_at": ended_at,
                    "scenes_count": scenes_reviewed
                })
                .eq("id", session_id)
                .execute()
            )
            
            if not update_result.data:
                raise Exception("Failed to update session record")
            
            # Return final session data
            return {
                "id": session["id"],
                "dataset_id": session["dataset_id"],
                "name": session["name"],
                "reviewer": session["reviewer_id"],
                "scenes_reviewed": scenes_reviewed,
                "started_at": datetime.fromisoformat(session["started_at"].replace('Z', '+00:00')),
                "ended_at": datetime.fromisoformat(ended_at.replace('Z', '+00:00'))
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to end review session {session_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to end review session")
    
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
            logger.error(f"Failed to apply scene corrections: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to apply scene corrections")
    
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
            logger.error(f"Failed to apply object corrections: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to apply object corrections")
    
    async def apply_scene_review_status(self, scene_id: str, verdict: str) -> bool:
        """Update scene status based on review verdict"""
        try:
            # Map review verdict to scene status
            status_map = {
                "approve": "approved",
                "reject": "rejected", 
                "edit": "corrected"
            }
            
            new_status = status_map.get(verdict, "processed")
            
            # Update scene status
            result = (
                self.supabase.table("scenes")
                .update({"status": new_status})
                .eq("id", scene_id)
                .execute()
            )
            
            logger.info(f"Updated scene {scene_id} status to {new_status}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to update scene status for {scene_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to update scene status")
    
    async def apply_object_review_status(self, object_id: str, verdict: str) -> bool:
        """Update object status based on review verdict (placeholder for future use)"""
        try:
            # Objects don't have a status field in current schema
            # This method is a placeholder for future object status tracking
            logger.info(f"Object {object_id} reviewed with verdict: {verdict}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update object review status for {object_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to update object review status")
    
    async def get_review_stats(
        self, 
        dataset_id: Optional[str] = None,
        reviewer_id: Optional[str] = None,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive review statistics from database.
        
        Args:
            dataset_id: Optional dataset filter
            reviewer_id: Optional reviewer filter  
            time_range: Optional time range filter (unused for now)
            
        Returns:
            Dictionary with review statistics matching ReviewStats schema
        """
        try:
            logger.info(f"Fetching review stats - dataset: {dataset_id}, reviewer: {reviewer_id}")
            
            # Get total scenes count
            scenes_query = self.supabase.table("scenes").select("id, status")
            if dataset_id:
                scenes_query = scenes_query.eq("dataset_id", dataset_id)
            
            scenes_result = scenes_query.execute()
            total_scenes = len(scenes_result.data)
            
            # Count scenes by status
            scene_status_counts = {}
            for scene in scenes_result.data:
                status = scene.get("status", "unprocessed")
                scene_status_counts[status] = scene_status_counts.get(status, 0) + 1
            
            # Get review counts  
            reviews_query = self.supabase.table("reviews").select("id, target, verdict, created_at")
            if reviewer_id:
                reviews_query = reviews_query.eq("reviewer_id", reviewer_id)
            
            reviews_result = reviews_query.execute()
            total_reviews = len(reviews_result.data)
            
            # Count reviews by verdict
            review_verdict_counts = {}
            for review in reviews_result.data:
                verdict = review.get("verdict", "approve")
                review_verdict_counts[verdict] = review_verdict_counts.get(verdict, 0) + 1
            
            # Calculate statistics
            approved_scenes = scene_status_counts.get("approved", 0)
            rejected_scenes = scene_status_counts.get("rejected", 0) 
            corrected_scenes = scene_status_counts.get("corrected", 0)
            processed_scenes = scene_status_counts.get("processed", 0)
            
            # Total reviewed = approved + rejected + corrected
            reviewed_scenes = approved_scenes + rejected_scenes + corrected_scenes
            pending_scenes = total_scenes - reviewed_scenes
            
            # Calculate review rate
            review_rate = (reviewed_scenes / total_scenes * 100) if total_scenes > 0 else 0.0
            
            # Calculate average time per scene based on real review data
            avg_time_per_scene = await self._calculate_avg_review_time()
            
            stats = {
                "total_scenes": total_scenes,
                "reviewed_scenes": reviewed_scenes, 
                "pending_scenes": max(0, pending_scenes),
                "approved_scenes": approved_scenes,
                "rejected_scenes": rejected_scenes,
                "corrected_scenes": corrected_scenes,
                "review_rate": round(review_rate, 1),
                "avg_time_per_scene": avg_time_per_scene
            }
            
            logger.info(f"Review stats calculated: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get review stats: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to retrieve review statistics")
    
    async def _calculate_avg_review_time(self) -> float:
        """Calculate average review time from database records"""
        try:
            # Get reviews with timing data
            reviews_result = (
                self.supabase.table("reviews")
                .select("review_time_seconds")
                .not_.is_("review_time_seconds", "null")
                .execute()
            )
            
            if not reviews_result.data:
                # No timing data available, return reasonable default
                return 45.0
            
            times = [r["review_time_seconds"] for r in reviews_result.data if r["review_time_seconds"] and r["review_time_seconds"] > 0]
            
            if not times:
                return 45.0
                
            avg_time = sum(times) / len(times)
            return round(avg_time, 1)
            
        except Exception as e:
            logger.warning(f"Could not calculate avg review time: {e}")
            return 45.0  # Fallback default