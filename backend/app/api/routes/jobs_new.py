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
    context: Optional[dict] = None

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
    limit: int = Query(100, ge=1, le=1000, description="Max log entries"),
    level: Optional[str] = Query(None, regex="^(DEBUG|INFO|WARNING|ERROR)$"),
    offset: int = Query(0, ge=0)
):
    """Get job logs from Supabase database"""
    try:
        from app.core.supabase import get_supabase
        
        supabase = get_supabase()
        
        # First, verify the job exists
        job_result = supabase.table("jobs").select("*").eq("id", job_id).execute()
        
        # Check if job_result is None or has no data
        if not job_result or not job_result.data or len(job_result.data) == 0:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = job_result.data[0]
        logs = []
        
        # Get actual job events from the job_events table
        events_query = supabase.table("job_events").select("*").eq("job_id", job_id).order("at", desc=False)
        
        # Apply timestamp filter if provided
        if since:
            events_query = events_query.gte("at", since.isoformat())
        
        events_result = events_query.execute()
        
        # Convert job events to log entries
        if events_result and events_result.data:
            for event in events_result.data:
                event_data = event.get("data", {}) if event.get("data") else {}
                
                # Determine log level based on event name
                event_name = event.get("name", "unknown")
                if "error" in event_name.lower() or "fail" in event_name.lower():
                    log_level = "ERROR"
                elif "warning" in event_name.lower() or "retry" in event_name.lower():
                    log_level = "WARNING"
                elif "debug" in event_name.lower():
                    log_level = "DEBUG"
                else:
                    log_level = "INFO"
                
                # Create log message from event
                message = f"Job event: {event_name}"
                if event_data:
                    if "message" in event_data:
                        message = event_data["message"]
                    elif "status" in event_data:
                        message = f"{event_name}: {event_data['status']}"
                    elif "count" in event_data:
                        message = f"{event_name}: {event_data['count']} items"
                
                logs.append(JobLogEntry(
                    timestamp=datetime.fromisoformat(event.get("at", "").replace('Z', '+00:00')),
                    level=log_level,
                    message=message,
                    scene_id=event_data.get("scene_id"),
                    stage=event_name,
                    context=event_data
                ))
        
        # If no events found, generate basic logs from job metadata
        if not logs:
            created_at = job.get("created_at")
            started_at = job.get("started_at") 
            finished_at = job.get("finished_at")
            status = job.get("status", "queued")
            error = job.get("error")
            meta = job.get("meta", {}) if job.get("meta") is not None else {}
            
            # Job creation log
            if created_at:
                logs.append(JobLogEntry(
                    timestamp=datetime.fromisoformat(created_at.replace('Z', '+00:00')),
                    level="INFO",
                    message=f"Job created for dataset processing",
                    context={"job_id": job_id, "kind": job.get("kind", "unknown")}
                ))
            
            # HuggingFace processing logs from metadata
            hf_url = meta.get("hf_url") if meta else None
            if hf_url:
                timestamp_str = started_at or created_at
                logs.append(JobLogEntry(
                    timestamp=datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')),
                    level="INFO", 
                    message=f"Loading HuggingFace dataset: {hf_url}",
                    context={"dataset_url": hf_url}
                ))
            
            # Job start log
            if started_at:
                logs.append(JobLogEntry(
                    timestamp=datetime.fromisoformat(started_at.replace('Z', '+00:00')),
                    level="INFO",
                    message="Job processing started",
                    context={"celery_task_id": meta.get("celery_task_id") if meta else None}
                ))
            
            # Processing progress from metadata
            processed_scenes = meta.get("processed_scenes", 0) if meta else 0
            failed_scenes = meta.get("failed_scenes", 0) if meta else 0
            
            if processed_scenes > 0 or failed_scenes > 0:
                timestamp_str = finished_at or started_at or created_at
                logs.append(JobLogEntry(
                    timestamp=datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')),
                    level="INFO" if failed_scenes == 0 else "WARNING",
                    message=f"Processed {processed_scenes} scenes successfully, {failed_scenes} failed",
                    context={
                        "processed_scenes": processed_scenes,
                        "failed_scenes": failed_scenes
                    }
                ))
            
            # Job completion/failure logs
            if status == "succeeded" and finished_at:
                logs.append(JobLogEntry(
                    timestamp=datetime.fromisoformat(finished_at.replace('Z', '+00:00')),
                    level="INFO",
                    message=f"Job completed successfully! Processed {processed_scenes} scenes.",
                    context={"final_status": status, "total_processed": processed_scenes}
                ))
            elif status == "failed":
                timestamp_str = finished_at or started_at or created_at
                logs.append(JobLogEntry(
                    timestamp=datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')),
                    level="ERROR", 
                    message=error or "Job failed with unknown error",
                    context={"error_details": error}
                ))
            elif status == "running":
                timestamp_str = started_at or created_at
                logs.append(JobLogEntry(
                    timestamp=datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')),
                    level="INFO",
                    message="Job is currently processing...",
                    context={"current_status": status}
                ))
        
        # Filter by level if specified
        if level:
            logs = [log for log in logs if log.level == level]
        
        # Filter by timestamp if since is provided (additional filtering)
        if since:
            logs = [log for log in logs if log.timestamp > since]
        
        # Sort by timestamp
        logs.sort(key=lambda x: x.timestamp)
        
        # Apply pagination
        total = len(logs)
        logs = logs[offset:offset + limit]
        
        return JobLogs(
            job_id=job_id,
            logs=logs,
            total=total,
            has_more=offset + len(logs) < total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch job logs for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch job logs: {str(e)}")