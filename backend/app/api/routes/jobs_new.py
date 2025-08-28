"""
Job management endpoints using Supabase
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.jobs import JobService
from app.schemas.database import Job, JobCreate, JobEvent
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Response schemas to match React expectations
class JobStats(BaseModel):
    total_jobs: int
    queued_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    cancelled_jobs: int
    avg_processing_time: Optional[float] = None
    success_rate: Optional[float] = None

class JobLogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    scene_id: Optional[str] = None
    stage: Optional[str] = None

class JobLogs(BaseModel):
    job_id: str
    logs: list[JobLogEntry]
    total: int
    has_more: bool

@router.get("")
async def get_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    kind: Optional[str] = Query(None, description="Filter by job kind"),
    dataset_id: Optional[str] = Query(None, description="Filter by dataset"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE, description="Items per page")
):
    """Get paginated list of jobs with optional filters"""
    try:
        service = JobService()
        result = await service.get_jobs(
            page=page,
            per_page=limit,
            status=status,
            kind=kind,
            dataset_id=dataset_id
        )
        
        return {
            "items": result["data"],
            "total": result["total_count"],
            "page": page,
            "limit": limit,
            "pages": result["total_pages"],
            "has_next": page < result["total_pages"],
            "has_prev": page > 1
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch jobs")

@router.get("/stats", response_model=JobStats)
async def get_job_stats(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset")
):
    """Get job statistics"""
    try:
        service = JobService()
        stats = await service.get_job_stats(dataset_id)
        
        return JobStats(**stats)
        
    except Exception as e:
        logger.error(f"Failed to fetch job stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch job stats")

@router.get("/{job_id}", response_model=Job)
async def get_job(job_id: str):
    """Get job by ID"""
    try:
        service = JobService()
        job = await service.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch job")

@router.post("", response_model=Job)
async def create_job(job_data: JobCreate):
    """Create a new processing job"""
    try:
        service = JobService()
        job = await service.create_job(job_data)
        
        # Add initial event
        await service.add_job_event(job.id, "created", {"kind": job.kind})
        
        logger.info(f"Created job: {job.id} ({job.kind})")
        return job
        
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create job")

@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running or queued job"""
    try:
        service = JobService()
        
        # Check if job exists and can be cancelled
        job = await service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status not in ["queued", "running"]:
            raise HTTPException(status_code=400, detail="Job cannot be cancelled")
        
        # Cancel the job
        success = await service.cancel_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Add cancellation event
        await service.add_job_event(job_id, "cancelled", {"reason": "user_request"})
        
        logger.info(f"Cancelled job: {job_id}")
        return {"message": "Job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel job")

@router.post("/{job_id}/retry", response_model=Job)
async def retry_job(job_id: str):
    """Retry a failed job"""
    try:
        service = JobService()
        
        # Check if job exists and can be retried
        job = await service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != "failed":
            raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
        
        # Reset job status
        updates = {
            "status": "queued",
            "error": None,
            "started_at": None,
            "finished_at": None
        }
        
        updated_job = await service.update_job(job_id, updates)
        if not updated_job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Add retry event
        await service.add_job_event(job_id, "retried", {"previous_error": job.error})
        
        logger.info(f"Retrying job: {job_id}")
        return updated_job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retry job")

@router.get("/{job_id}/logs", response_model=JobLogs)
async def get_job_logs(
    job_id: str,
    since: Optional[datetime] = Query(None, description="Get logs since timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Max log entries")
):
    """Get job logs from events"""
    try:
        service = JobService()
        
        # Verify job exists
        job = await service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get job events
        events = await service.get_job_events(job_id, limit, since)
        
        # Convert events to log entries
        logs = []
        for event in events:
            level = "ERROR" if event.name in ["failed", "error"] else "INFO"
            message = f"Job {event.name}"
            if event.data:
                if "error" in event.data:
                    message += f": {event.data['error']}"
                elif "stage" in event.data:
                    message += f" - {event.data['stage']}"
            
            logs.append(JobLogEntry(
                timestamp=event.at,
                level=level,
                message=message,
                scene_id=event.data.get("scene_id") if event.data else None,
                stage=event.data.get("stage") if event.data else None
            ))
        
        return JobLogs(
            job_id=job_id,
            logs=logs,
            total=len(logs),
            has_more=len(logs) == limit  # Simple heuristic
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch job logs for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch job logs")