"""
Review workflow endpoints using Supabase
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.reviews import ReviewService
from app.schemas.database import Review, ReviewCreate

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response schemas to match React expectations
class BatchReviewCreate(BaseModel):
    scene_reviews: List[Dict[str, Any]]

class ReviewSessionCreate(BaseModel):
    dataset_id: Optional[str] = None
    name: Optional[str] = None

class ReviewSession(BaseModel):
    id: str
    dataset_id: Optional[str] = None
    name: Optional[str] = None
    reviewer: Optional[str] = None
    scenes_reviewed: int
    started_at: datetime
    ended_at: Optional[datetime] = None

class ReviewProgressStats(BaseModel):
    total_scenes: int
    pending_scenes: int
    approved_scenes: int
    rejected_scenes: int
    corrected_scenes: int
    completion_rate: float

class ReviewStats(BaseModel):
    total_scenes: int
    reviewed_scenes: int
    pending_scenes: int
    approved_scenes: int
    rejected_scenes: int
    corrected_scenes: int
    review_rate: float
    avg_time_per_scene: float

@router.post("", response_model=Review)
async def create_review(review_data: ReviewCreate):
    """Create a new review/annotation"""
    try:
        service = ReviewService()
        review = await service.create_review(review_data)
        
        # Apply corrections if this is an edit
        if review.verdict == "edit" and review.after_json:
            if review.target == "scene":
                await service.apply_scene_corrections(review.target_id, review.after_json)
            elif review.target == "object":
                await service.apply_object_corrections(review.target_id, review.after_json)
        
        logger.info(f"Created review: {review.id} ({review.verdict})")
        return review
        
    except Exception as e:
        logger.error(f"Failed to create review: {e}")
        raise HTTPException(status_code=500, detail="Failed to create review")

@router.post("/batch")
async def create_batch_reviews(batch_data: BatchReviewCreate):
    """Create multiple scene reviews in a batch"""
    try:
        service = ReviewService()
        review_ids = await service.create_batch_reviews(batch_data.scene_reviews)
        
        logger.info(f"Created {len(review_ids)} batch reviews")
        return {
            "message": f"Created {len(review_ids)} reviews",
            "review_ids": review_ids
        }
        
    except Exception as e:
        logger.error(f"Failed to create batch reviews: {e}")
        raise HTTPException(status_code=500, detail="Failed to create batch reviews")

@router.get("/progress", response_model=ReviewProgressStats)
async def get_review_progress(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset")
):
    """Get review progress statistics"""
    try:
        service = ReviewService()
        stats = await service.get_review_progress(dataset_id)
        
        return ReviewProgressStats(**stats)
        
    except Exception as e:
        logger.error(f"Failed to fetch review progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch review progress")

@router.post("/sessions", response_model=ReviewSession)
async def start_review_session(session_data: ReviewSessionCreate):
    """Start a new review session"""
    try:
        service = ReviewService()
        session = await service.start_review_session(
            dataset_id=session_data.dataset_id,
            reviewer_id="anonymous"  # TODO: Get from auth context
        )
        
        logger.info(f"Started review session: {session['id']}")
        return ReviewSession(**session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start review session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start review session")

@router.post("/sessions/{session_id}/end", response_model=ReviewSession)
async def end_review_session(session_id: str):
    """End a review session"""
    try:
        service = ReviewService()
        session = await service.end_review_session(session_id)
        
        logger.info(f"Ended review session: {session_id}")
        return ReviewSession(**session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end review session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to end review session")

@router.get("/stats", response_model=ReviewStats)
async def get_review_stats(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    reviewer_id: Optional[str] = Query(None, description="Filter by reviewer ID"),
    time_range: Optional[str] = Query(None, description="Time range filter")
):
    """Get review statistics from database"""
    try:
        service = ReviewService()
        
        # Get real review statistics from database
        stats = await service.get_review_stats(
            dataset_id=dataset_id,
            reviewer_id=reviewer_id, 
            time_range=time_range
        )
        
        return ReviewStats(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get review stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get review stats")

# Frontend-compatible endpoints
@router.post("/scenes")
async def submit_scene_review(review: Dict[str, Any]):
    """Submit a scene review (frontend compatibility)"""
    try:
        service = ReviewService()
        scene_id = review.get("scene_id")
        status = review.get("status")
        notes = review.get("notes")
        
        if not scene_id or not status:
            raise HTTPException(status_code=400, detail="scene_id and status are required")
        
        # Map status to verdict
        verdict_map = {
            "approved": "approve",
            "rejected": "reject", 
            "corrected": "edit"
        }
        verdict = verdict_map.get(status, "approve")
        
        # Handle corrections
        after_json = None
        if status == "corrected":
            corrections = {}
            if "corrected_scene_type" in review:
                corrections["scene_type"] = review["corrected_scene_type"]
            if "corrected_styles" in review:
                corrections["styles"] = review["corrected_styles"]
            after_json = corrections if corrections else None
        
        review_data = ReviewCreate(
            target="scene",
            target_id=scene_id,
            verdict=verdict,
            after_json=after_json,
            notes=notes
        )
        
        result = await service.create_review(review_data)
        
        # Apply corrections if this is an edit
        if verdict == "edit" and after_json:
            await service.apply_scene_corrections(scene_id, after_json)
        
        # Update scene status based on review verdict
        await service.apply_scene_review_status(scene_id, verdict)
        
        return {"message": f"Scene {status}", "review_id": str(result.id)}
        
    except Exception as e:
        logger.error(f"Failed to submit scene review: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit scene review")

@router.post("/objects")
async def submit_object_review(review: Dict[str, Any]):
    """Submit an object review (frontend compatibility)"""
    try:
        service = ReviewService()
        object_id = review.get("object_id")
        status = review.get("status")
        notes = review.get("notes")
        
        if not object_id or not status:
            raise HTTPException(status_code=400, detail="object_id and status are required")
        
        # Map status to verdict
        verdict_map = {
            "approved": "approve",
            "rejected": "reject",
            "corrected": "edit"
        }
        verdict = verdict_map.get(status, "approve")
        
        # Handle corrections
        after_json = None
        if status == "corrected":
            corrections = {}
            if "corrected_label" in review:
                corrections["category_code"] = review["corrected_label"]
            if "corrected_material" in review:
                corrections["material"] = review["corrected_material"]
            after_json = corrections if corrections else None
        
        review_data = ReviewCreate(
            target="object",
            target_id=object_id,
            verdict=verdict,
            after_json=after_json,
            notes=notes
        )
        
        result = await service.create_review(review_data)
        
        # Apply corrections if this is an edit
        if verdict == "edit" and after_json:
            await service.apply_object_corrections(object_id, after_json)
        
        # Update object status based on review verdict
        await service.apply_object_review_status(object_id, verdict)
        
        return {"message": f"Object {status}", "review_id": str(result.id)}
        
    except Exception as e:
        logger.error(f"Failed to submit object review: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit object review")

# Additional endpoints for workflow compatibility
@router.post("/scenes/{scene_id}/approve")
async def approve_scene(scene_id: str, notes: Optional[str] = None):
    """Quick approve a scene"""
    try:
        service = ReviewService()
        
        review_data = ReviewCreate(
            target="scene",
            target_id=scene_id,
            verdict="approve",
            notes=notes
        )
        
        review = await service.create_review(review_data)
        
        # Update scene status to approved
        await service.apply_scene_review_status(scene_id, "approve")
        
        return {"message": "Scene approved", "review_id": review.id}
        
    except Exception as e:
        logger.error(f"Failed to approve scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve scene")

@router.post("/scenes/{scene_id}/reject")
async def reject_scene(scene_id: str, notes: Optional[str] = None):
    """Quick reject a scene"""
    try:
        service = ReviewService()
        
        review_data = ReviewCreate(
            target="scene",
            target_id=scene_id,
            verdict="reject",
            notes=notes
        )
        
        review = await service.create_review(review_data)
        
        # Update scene status to rejected
        await service.apply_scene_review_status(scene_id, "reject")
        
        return {"message": "Scene rejected", "review_id": review.id}
        
    except Exception as e:
        logger.error(f"Failed to reject scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject scene")

@router.post("/scenes/{scene_id}/correct")
async def correct_scene(
    scene_id: str, 
    corrections: Dict[str, Any],
    notes: Optional[str] = None
):
    """Apply corrections to a scene"""
    try:
        service = ReviewService()
        
        # Get current scene data as "before"
        from app.services.scenes import SceneService
        scene_service = SceneService()
        current_scene = await scene_service.get_scene(scene_id, include_objects=False)
        
        review_data = ReviewCreate(
            target="scene",
            target_id=scene_id,
            verdict="edit",
            before_json=current_scene,
            after_json=corrections,
            notes=notes
        )
        
        review = await service.create_review(review_data)
        
        # Apply the corrections
        await service.apply_scene_corrections(scene_id, corrections)
        
        return {"message": "Scene corrected", "review_id": review.id}
        
    except Exception as e:
        logger.error(f"Failed to correct scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to correct scene")

@router.post("/objects/{object_id}/correct")
async def correct_object(
    object_id: str,
    corrections: Dict[str, Any], 
    notes: Optional[str] = None
):
    """Apply corrections to an object"""
    try:
        service = ReviewService()
        
        review_data = ReviewCreate(
            target="object",
            target_id=object_id,
            verdict="edit",
            after_json=corrections,
            notes=notes
        )
        
        review = await service.create_review(review_data)
        
        # Apply the corrections
        await service.apply_object_corrections(object_id, corrections)
        
        return {"message": "Object corrected", "review_id": review.id}
        
    except Exception as e:
        logger.error(f"Failed to correct object {object_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to correct object")