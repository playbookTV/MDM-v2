"""
Job management endpoints
"""

import uuid
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.dataset import Job, Dataset
from app.schemas.job import (
    Job as JobSchema,
    JobCreate,
    JobStats,
    JobLogEntry,
    JobLogs
)
from app.schemas.common import Page
from app.services.queue import QueueService
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("", response_model=Page[JobSchema])
async def get_jobs(
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    kind: Optional[str] = Query(None, description="Filter by job kind"),
    dataset_id: Optional[str] = Query(None, description="Filter by dataset"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE, description="Items per page")
):
    """Get paginated list of jobs with optional filters"""
    try:
        offset = (page - 1) * limit
        
        # Build query
        query = select(Job).order_by(desc(Job.created_at))
        count_query = select(func.count(Job.id))
        
        # Apply filters
        filters = []
        if status:
            filters.append(Job.status == status)
        if kind:
            filters.append(Job.kind == kind)
        if dataset_id:
            filters.append(Job.dataset_id == dataset_id)
        
        if filters:
            combined_filter = and_(*filters)
            query = query.where(combined_filter)
            count_query = count_query.where(combined_filter)
        
        # Execute queries
        total = await db.scalar(count_query)
        result = await db.execute(query.offset(offset).limit(limit))
        jobs = result.scalars().all()
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        
        return Page(
            items=jobs,
            total=total,
            page=page,
            limit=limit,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch jobs")

@router.get("/{job_id}", response_model=JobSchema)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get job by ID"""
    try:
        query = select(Job).where(Job.id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch job")

@router.post("", response_model=JobSchema)
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new processing job"""
    try:
        # Verify dataset exists
        query = select(Dataset).where(Dataset.id == job_data.dataset_id)
        result = await db.execute(query)
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Count scenes in dataset for total_items
        scene_count_query = select(func.count()).select_from(
            select(1).where(
                # TODO: Add Scene import and proper query
                # For now using a placeholder
            )
        )
        # Simplified for now - in production would count actual scenes
        total_items = dataset.total_scenes
        
        # Create job record
        job = Job(
            id=str(uuid.uuid4()),
            dataset_id=job_data.dataset_id,
            name=job_data.name,
            kind=job_data.kind,
            status="queued",
            total_items=total_items,
            completed_items=0,
            failed_items=0,
            config=job_data.config,
            result={},
        )
        
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        # TODO: Enqueue job to Redis
        # For now we'll just create the record
        # queue_service = QueueService()
        # await queue_service.enqueue_job(job.id, job_data.dataset_id, job_data.config)
        
        logger.info(f"Created job: {job.id} ({job.kind}) for dataset {job_data.dataset_id}")
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create job")

@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running or queued job"""
    try:
        query = select(Job).where(Job.id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status not in ["queued", "running"]:
            raise HTTPException(status_code=400, detail="Job cannot be cancelled")
        
        # Update job status
        job.status = "cancelled"
        job.completed_at = datetime.utcnow()
        
        await db.commit()
        
        # TODO: Signal Redis queue to cancel job
        # queue_service = QueueService()
        # await queue_service.cancel_job(job_id)
        
        logger.info(f"Cancelled job: {job_id}")
        return {"message": "Job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to cancel job")

@router.post("/{job_id}/retry", response_model=JobSchema)
async def retry_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retry a failed job"""
    try:
        query = select(Job).where(Job.id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != "failed":
            raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
        
        # Reset job status
        job.status = "queued"
        job.failed_items = 0
        job.error_message = None
        job.started_at = None
        job.completed_at = None
        
        await db.commit()
        await db.refresh(job)
        
        # TODO: Re-enqueue job to Redis
        # queue_service = QueueService()
        # await queue_service.enqueue_job(job.id, job.dataset_id, job.config)
        
        logger.info(f"Retrying job: {job_id}")
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry job {job_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to retry job")

@router.get("/stats", response_model=JobStats)
async def get_job_stats(
    db: AsyncSession = Depends(get_db),
    dataset_id: Optional[str] = Query(None, description="Filter by dataset")
):
    """Get job statistics"""
    try:
        # Build base query
        base_query = select(Job)
        if dataset_id:
            base_query = base_query.where(Job.dataset_id == dataset_id)
        
        # Get counts by status
        stats_query = select(
            func.count(Job.id).label('total'),
            func.sum(func.case((Job.status == 'queued', 1), else_=0)).label('queued'),
            func.sum(func.case((Job.status == 'running', 1), else_=0)).label('running'),
            func.sum(func.case((Job.status == 'completed', 1), else_=0)).label('completed'),
            func.sum(func.case((Job.status == 'failed', 1), else_=0)).label('failed'),
            func.sum(func.case((Job.status == 'cancelled', 1), else_=0)).label('cancelled'),
            func.avg(
                func.extract('epoch', Job.completed_at - Job.started_at)
            ).label('avg_duration')
        )
        
        if dataset_id:
            stats_query = stats_query.where(Job.dataset_id == dataset_id)
        
        result = await db.execute(stats_query)
        row = result.first()
        
        # Calculate success rate
        total_finished = (row.completed or 0) + (row.failed or 0)
        success_rate = None
        if total_finished > 0:
            success_rate = ((row.completed or 0) / total_finished) * 100
        
        return JobStats(
            total_jobs=row.total or 0,
            queued_jobs=row.queued or 0,
            running_jobs=row.running or 0,
            completed_jobs=row.completed or 0,
            failed_jobs=row.failed or 0,
            cancelled_jobs=row.cancelled or 0,
            avg_processing_time=row.avg_duration,
            success_rate=success_rate
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch job stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch job stats")

@router.get("/{job_id}/logs", response_model=JobLogs)
async def get_job_logs(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    since: Optional[datetime] = Query(None, description="Get logs since timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Max log entries")
):
    """Get job logs (placeholder - would use Redis streams in production)"""
    try:
        query = select(Job).where(Job.id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # TODO: In production, fetch logs from Redis streams
        # For now, return mock logs based on job status
        logs = []
        
        if job.status != "queued":
            logs.append(JobLogEntry(
                timestamp=job.created_at,
                level="INFO",
                message="Job created and queued"
            ))
        
        if job.started_at:
            logs.append(JobLogEntry(
                timestamp=job.started_at,
                level="INFO",
                message="Job started processing"
            ))
        
        if job.status == "completed" and job.completed_at:
            logs.append(JobLogEntry(
                timestamp=job.completed_at,
                level="INFO",
                message=f"Job completed successfully. Processed {job.completed_items} items."
            ))
        elif job.status == "failed":
            logs.append(JobLogEntry(
                timestamp=job.updated_at or job.created_at,
                level="ERROR",
                message=job.error_message or "Job failed with unknown error"
            ))
        
        return JobLogs(
            job_id=job_id,
            logs=logs[-limit:],
            total=len(logs),
            has_more=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch job logs for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch job logs")