"""
Job-related Pydantic schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Job schemas
class JobBase(BaseModel):
    """Base job fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Job name")
    kind: str = Field(..., description="Job type")

class JobCreate(JobBase):
    """Create job request"""
    dataset_id: str = Field(..., description="Dataset ID")
    config: Dict[str, Any] = Field(default_factory=dict, description="Job configuration")

class Job(JobBase):
    """Job response model"""
    id: str = Field(..., description="Job ID")
    dataset_id: str = Field(..., description="Dataset ID")
    status: str = Field(..., description="Job status")
    total_items: int = Field(..., description="Total items to process")
    completed_items: int = Field(..., description="Completed items")
    failed_items: int = Field(..., description="Failed items")
    config: Dict[str, Any] = Field(..., description="Job configuration")
    result: Dict[str, Any] = Field(..., description="Job result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True

class JobStats(BaseModel):
    """Job statistics"""
    total_jobs: int = Field(..., description="Total number of jobs")
    queued_jobs: int = Field(..., description="Queued jobs")
    running_jobs: int = Field(..., description="Running jobs")
    completed_jobs: int = Field(..., description="Completed jobs")
    failed_jobs: int = Field(..., description="Failed jobs")
    cancelled_jobs: int = Field(..., description="Cancelled jobs")
    
    # Performance metrics
    avg_processing_time: Optional[float] = Field(None, description="Average processing time in seconds")
    success_rate: Optional[float] = Field(None, description="Success rate as percentage")

class JobLogEntry(BaseModel):
    """Single job log entry"""
    timestamp: datetime = Field(..., description="Log timestamp")
    level: str = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    scene_id: Optional[str] = Field(None, description="Scene ID if applicable")
    stage: Optional[str] = Field(None, description="Processing stage")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context data")

class JobLogs(BaseModel):
    """Job logs response"""
    job_id: str = Field(..., description="Job ID")
    logs: List[JobLogEntry] = Field(..., description="Log entries")
    total: int = Field(..., description="Total log entries")
    has_more: bool = Field(..., description="Whether there are more logs")