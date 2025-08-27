"""
Review-related Pydantic schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Review schemas
class ReviewBase(BaseModel):
    """Base review fields"""
    action: str = Field(..., description="Review action: approve, reject, correct")
    notes: Optional[str] = Field(None, description="Review notes")

class ReviewCreate(ReviewBase):
    """Create review request"""
    scene_id: Optional[str] = Field(None, description="Scene ID (for scene reviews)")
    object_id: Optional[str] = Field(None, description="Object ID (for object reviews)")
    changes: Dict[str, Any] = Field(default_factory=dict, description="Changes made")

class Review(ReviewBase):
    """Review response model"""
    id: str = Field(..., description="Review ID")
    scene_id: Optional[str] = Field(None, description="Scene ID")
    object_id: Optional[str] = Field(None, description="Object ID")
    changes: Dict[str, Any] = Field(..., description="Changes made")
    session_id: Optional[str] = Field(None, description="Review session ID")
    reviewer: Optional[str] = Field(None, description="Reviewer name")
    created_at: datetime = Field(..., description="Review timestamp")

    class Config:
        from_attributes = True

class BatchReviewCreate(BaseModel):
    """Batch review request"""
    scene_reviews: List[Dict[str, Any]] = Field(..., description="Scene review data")

class ReviewSessionCreate(BaseModel):
    """Review session create request"""
    dataset_id: Optional[str] = Field(None, description="Dataset to review")
    name: Optional[str] = Field(None, description="Session name")

class ReviewSession(BaseModel):
    """Review session response"""
    id: str = Field(..., description="Session ID")
    dataset_id: Optional[str] = Field(None, description="Dataset ID")
    name: Optional[str] = Field(None, description="Session name")
    reviewer: Optional[str] = Field(None, description="Reviewer name")
    scenes_reviewed: int = Field(..., description="Number of scenes reviewed")
    started_at: datetime = Field(..., description="Session start time")
    ended_at: Optional[datetime] = Field(None, description="Session end time")

class ReviewProgressStats(BaseModel):
    """Review progress statistics"""
    total_scenes: int = Field(..., description="Total scenes")
    pending_scenes: int = Field(..., description="Pending review")
    approved_scenes: int = Field(..., description="Approved scenes")
    rejected_scenes: int = Field(..., description="Rejected scenes")
    corrected_scenes: int = Field(..., description="Corrected scenes")
    completion_rate: float = Field(..., description="Completion rate percentage")