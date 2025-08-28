"""
Queue management and monitoring endpoints
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.redis import RedisQueue, RedisEventStream, get_redis
from app.services.jobs import JobService

logger = logging.getLogger(__name__)
router = APIRouter()

class QueueStatus(BaseModel):
    redis_connected: bool
    queue_length: int
    active_workers: int = 0  # Mock for now
    
class JobQueueCreate(BaseModel):
    job_id: str
    kind: str
    dataset_id: str = None
    options: Dict[str, Any] = None

@router.get("/status")
async def get_queue_status():
    """Get current queue status"""
    try:
        redis_client = get_redis()
        redis_connected = redis_client is not None
        
        queue = RedisQueue()
        queue_length = await queue.get_queue_length()
        
        return QueueStatus(
            redis_connected=redis_connected,
            queue_length=queue_length,
            active_workers=0  # TODO: Get from Celery
        )
        
    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        return QueueStatus(
            redis_connected=False,
            queue_length=0,
            active_workers=0
        )

@router.post("/test-job")
async def create_test_job():
    """Create a test job for queue testing"""
    try:
        from app.schemas.database import JobCreate
        from uuid import uuid4
        
        # Create test job with null dataset_id for testing
        job_service = JobService()
        test_job_data = JobCreate(
            kind="process",
            dataset_id=None,  # Null dataset_id for testing
            meta={"test": True, "scene_id": str(uuid4())}
        )
        
        job = await job_service.create_job(test_job_data)
        
        return {
            "message": "Test job created and queued",
            "job_id": job.id,
            "status": job.status
        }
        
    except Exception as e:
        logger.error(f"Failed to create test job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create test job")

@router.get("/workers")
async def get_worker_status():
    """Get Celery worker status (placeholder)"""
    try:
        # TODO: Integrate with Celery inspect
        return {
            "active_workers": 0,
            "available_queues": ["dataset_processing", "scene_processing", "maintenance"],
            "redis_connected": get_redis() is not None
        }
        
    except Exception as e:
        logger.error(f"Failed to get worker status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get worker status")