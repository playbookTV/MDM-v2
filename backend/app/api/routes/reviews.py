"""
Review workflow endpoints
"""

import uuid
import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.dataset import Review, Scene, SceneObject
from app.schemas.review import (
    Review as ReviewSchema,
    ReviewCreate,
    BatchReviewCreate,
    ReviewSessionCreate,
    ReviewSession,
    ReviewProgressStats
)
from app.schemas.common import Page

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("", response_model=ReviewSchema)
async def create_review(
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new review/annotation"""
    try:
        # Validate that either scene_id or object_id is provided
        if not review_data.scene_id and not review_data.object_id:
            raise HTTPException(
                status_code=400,
                detail="Either scene_id or object_id must be provided"
            )
        
        # Create review record
        review = Review(
            id=str(uuid.uuid4()),
            scene_id=review_data.scene_id,
            object_id=review_data.object_id,
            action=review_data.action,
            changes=review_data.changes,
            notes=review_data.notes,
            reviewer="anonymous",  # TODO: Get from auth context
        )
        
        db.add(review)
        
        # Update scene/object review status
        if review_data.scene_id:
            scene_query = select(Scene).where(Scene.id == review_data.scene_id)
            scene_result = await db.execute(scene_query)
            scene = scene_result.scalar_one_or_none()
            
            if scene:
                scene.review_status = review_data.action if review_data.action in ['approved', 'rejected', 'corrected'] else 'pending'
                scene.review_notes = review_data.notes
                scene.reviewed_by = "anonymous"  # TODO: Get from auth
                scene.reviewed_at = datetime.utcnow()
                
                # Apply changes if action is 'correct'
                if review_data.action == 'correct' and review_data.changes:
                    for field, value in review_data.changes.items():
                        if hasattr(scene, field):
                            setattr(scene, field, value)
        
        if review_data.object_id:
            obj_query = select(SceneObject).where(SceneObject.id == review_data.object_id)
            obj_result = await db.execute(obj_query)
            obj = obj_result.scalar_one_or_none()
            
            if obj:
                obj.review_status = review_data.action if review_data.action in ['approved', 'rejected', 'corrected'] else 'pending'
                obj.review_notes = review_data.notes
                
                # Apply changes if action is 'correct'
                if review_data.action == 'correct' and review_data.changes:
                    for field, value in review_data.changes.items():
                        if hasattr(obj, field):
                            setattr(obj, field, value)
        
        await db.commit()
        await db.refresh(review)
        
        logger.info(f"Created review: {review.id} ({review.action})")
        return review
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create review: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create review")

@router.post("/batch", response_model=dict)
async def create_batch_reviews(
    batch_data: BatchReviewCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create multiple scene reviews in a batch"""
    try:
        created_reviews = []
        
        for scene_review in batch_data.scene_reviews:
            # Create review record
            review = Review(
                id=str(uuid.uuid4()),
                scene_id=scene_review.get('scene_id'),
                action=scene_review.get('status', 'approved'),
                changes={},
                notes=scene_review.get('notes'),
                reviewer="anonymous",  # TODO: Get from auth
            )
            
            db.add(review)
            created_reviews.append(review.id)
            
            # Update scene status
            if scene_review.get('scene_id'):
                scene_query = select(Scene).where(Scene.id == scene_review['scene_id'])
                scene_result = await db.execute(scene_query)
                scene = scene_result.scalar_one_or_none()
                
                if scene:
                    scene.review_status = scene_review.get('status', 'approved')
                    scene.review_notes = scene_review.get('notes')
                    scene.reviewed_by = "anonymous"  # TODO: Get from auth
                    scene.reviewed_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Created {len(created_reviews)} batch reviews")
        return {
            "message": f"Created {len(created_reviews)} reviews",
            "review_ids": created_reviews
        }
        
    except Exception as e:
        logger.error(f"Failed to create batch reviews: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create batch reviews")

@router.get("/progress", response_model=ReviewProgressStats)
async def get_review_progress(
    db: AsyncSession = Depends(get_db),
    dataset_id: Optional[str] = Query(None, description="Filter by dataset")
):
    """Get review progress statistics"""
    try:
        # Build query
        base_query = select(Scene)
        if dataset_id:
            base_query = base_query.where(Scene.dataset_id == dataset_id)
        
        # Get counts by review status
        stats_query = select(
            func.count(Scene.id).label('total'),
            func.sum(func.case((Scene.review_status.is_(None), 1), else_=0)).label('pending'),
            func.sum(func.case((Scene.review_status == 'approved', 1), else_=0)).label('approved'),
            func.sum(func.case((Scene.review_status == 'rejected', 1), else_=0)).label('rejected'),
            func.sum(func.case((Scene.review_status == 'corrected', 1), else_=0)).label('corrected'),
        )
        
        if dataset_id:
            stats_query = stats_query.where(Scene.dataset_id == dataset_id)
        
        result = await db.execute(stats_query)
        row = result.first()
        
        total = row.total or 0
        pending = row.pending or 0
        approved = row.approved or 0
        rejected = row.rejected or 0
        corrected = row.corrected or 0
        
        # Calculate completion rate
        reviewed = approved + rejected + corrected
        completion_rate = (reviewed / total * 100) if total > 0 else 0
        
        return ReviewProgressStats(
            total_scenes=total,
            pending_scenes=pending,
            approved_scenes=approved,
            rejected_scenes=rejected,
            corrected_scenes=corrected,
            completion_rate=completion_rate
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch review progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch review progress")

@router.post("/sessions", response_model=ReviewSession)
async def start_review_session(
    session_data: ReviewSessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Start a new review session"""
    try:
        # For now, return a mock session
        # In production, this would create a session record and track reviewer activity
        session = {
            "id": str(uuid.uuid4()),
            "dataset_id": session_data.dataset_id,
            "name": session_data.name or "Review Session",
            "reviewer": "anonymous",
            "scenes_reviewed": 0,
            "started_at": datetime.utcnow(),
            "ended_at": None
        }
        
        logger.info(f"Started review session: {session['id']}")
        return ReviewSession(**session)
        
    except Exception as e:
        logger.error(f"Failed to start review session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start review session")

@router.post("/sessions/{session_id}/end", response_model=ReviewSession)
async def end_review_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """End a review session"""
    try:
        # For now, return a mock ended session  
        # In production, this would update the session record
        session = {
            "id": session_id,
            "dataset_id": None,
            "name": "Review Session",
            "reviewer": "anonymous", 
            "scenes_reviewed": 0,
            "started_at": datetime.utcnow(),
            "ended_at": datetime.utcnow()
        }
        
        logger.info(f"Ended review session: {session_id}")
        return ReviewSession(**session)
        
    except Exception as e:
        logger.error(f"Failed to end review session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to end review session")