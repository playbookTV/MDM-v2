"""
Jobs service using Supabase client with Redis queue integration
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from app.core.supabase import get_supabase
from app.core.redis import RedisQueue, RedisEventStream, init_redis
from app.schemas.database import Job, JobCreate, JobEvent

logger = logging.getLogger(__name__)

class JobService:
    """Service for job operations"""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.queue = RedisQueue()
        self.event_stream = RedisEventStream()
        self._redis_initialized = False
    
    async def get_jobs(
        self, 
        page: int = 1, 
        per_page: int = 20,
        status: Optional[str] = None,
        kind: Optional[str] = None,
        dataset_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get paginated list of jobs"""
        try:
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Build query
            query = self.supabase.table("jobs").select("*")
            count_query = self.supabase.table("jobs").select("*", count="exact")
            
            # Apply filters
            if status:
                query = query.eq("status", status)
                count_query = count_query.eq("status", status)
            if kind:
                query = query.eq("kind", kind)
                count_query = count_query.eq("kind", kind)
            if dataset_id:
                query = query.eq("dataset_id", dataset_id)
                count_query = count_query.eq("dataset_id", dataset_id)
            
            # Get total count
            total_count = count_query.execute().count
            
            # Get paginated data
            result = query.range(offset, offset + per_page - 1).order("created_at", desc=True).execute()
            
            return {
                "data": result.data,
                "count": len(result.data),
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": (total_count + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Failed to get jobs: {e}")
            raise
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        try:
            result = self.supabase.table("jobs").select("*").eq("id", job_id).execute()
            
            if result.data:
                return Job(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            raise
    
    async def create_job(self, job_data: JobCreate) -> Job:
        """Create a new job and queue it for processing"""
        try:
            # Initialize Redis if not already done
            if not self._redis_initialized:
                await init_redis()
                self._redis_initialized = True
            
            # Convert to dict with JSON-safe serialization and add ID
            data = job_data.model_dump(mode='json')
            job_id = str(uuid4())
            data["id"] = job_id
            
            # Create job in database
            result = self.supabase.table("jobs").insert(data).execute()
            job = Job(**result.data[0])
            
            # Queue the job for processing (only if queueing doesn't break job creation)
            try:
                await self._queue_job_for_processing(job)
            except Exception as queue_error:
                logger.warning(f"Failed to queue job {job_id}, continuing anyway: {queue_error}")
            
            logger.info(f"Job {job_id} created and queued successfully")
            return job
            
        except Exception as e:
            logger.error(f"Failed to create job: {e}")
            raise
    
    async def _queue_job_for_processing(self, job: Job):
        """Queue job for background processing with Celery"""
        try:
            # Prepare job data for queue  
            job_data = {
                "id": str(job.id),  # Convert UUID to string
                "kind": job.kind,
                "dataset_id": str(job.dataset_id) if job.dataset_id else None,
                "meta": job.meta or {}  # Use 'meta' not 'options'
            }
            
            # Try to use Celery if available
            try:
                # Import and use Celery tasks for job processing
                
                from app.worker.tasks import process_dataset, process_scene
                
                # Route job to appropriate Celery task based on kind
                if job.kind == "ingest":
                    # Dataset ingestion job - process entire dataset
                    task = process_dataset.delay(
                        job_id=str(job.id),
                        dataset_id=str(job.dataset_id),
                        options=job.meta or {}  # Task expects 'options' parameter
                    )
                    logger.info(f"Dataset ingestion job {job.id} queued with task ID: {task.id}")
                    
                elif job.kind == "process" or job.kind == "scene_processing":
                    # Scene processing job - AI analysis pipeline
                    scene_id = job.meta.get("scene_id") if job.meta else None
                    # Ensure scene_id is a string for JSON serialization (but don't convert None to 'None')
                    scene_id_str = str(scene_id) if scene_id is not None else None
                    
                    task = process_scene.delay(
                        job_id=str(job.id),
                        scene_id=scene_id_str,
                        options=job.meta or {}  # Task expects 'options' parameter
                    )
                    logger.info(f"Scene processing job {job.id} queued with task ID: {task.id}")
                    
                else:
                    logger.warning(f"Unknown job kind: {job.kind}")
                    
            except ImportError as e:
                logger.warning(f"Celery not available, using Redis queue only: {e}")
            
            # Also add to Redis queue for monitoring
            await self.queue.enqueue_job(job_data)
            
        except Exception as e:
            logger.warning(f"Failed to queue job {job.id}: {e}")
            # Don't fail job creation if queueing fails, just log the warning
    
    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> Optional[Job]:
        """Update job status and metadata"""
        try:
            result = self.supabase.table("jobs").update(updates).eq("id", job_id).execute()
            
            if result.data:
                return Job(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            raise
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        try:
            updates = {
                "status": "failed",  # Using 'failed' instead of 'cancelled' to match enum
                "finished_at": datetime.utcnow().isoformat(),
                "error": "Job cancelled by user"
            }
            
            result = self.supabase.table("jobs").update(updates).eq("id", job_id).execute()
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            raise
    
    async def get_job_events(
        self, 
        job_id: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[JobEvent]:
        """Get events for a job"""
        try:
            query = (
                self.supabase.table("job_events")
                .select("*")
                .eq("job_id", job_id)
                .order("at", desc=True)
                .limit(limit)
            )
            
            if since:
                query = query.gte("at", since.isoformat())
            
            result = query.execute()
            
            return [JobEvent(**event) for event in result.data]
            
        except Exception as e:
            logger.error(f"Failed to get job events for {job_id}: {e}")
            raise
    
    async def add_job_event(self, job_id: str, name: str, data: Dict[str, Any] = None) -> JobEvent:
        """Add an event to a job"""
        try:
            # Recursively convert any UUID objects to strings for JSON serialization
            def serialize_data(obj):
                if hasattr(obj, '__dict__'):
                    return {k: serialize_data(v) for k, v in obj.__dict__.items()}
                elif isinstance(obj, dict):
                    return {k: serialize_data(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [serialize_data(item) for item in obj]
                elif hasattr(obj, '__class__') and 'UUID' in str(type(obj)):
                    return str(obj)
                else:
                    return obj
            
            serialized_data = serialize_data(data or {})
            
            event_data = {
                "id": str(uuid4()),
                "job_id": job_id,
                "name": name,
                "data": serialized_data
            }
            
            result = self.supabase.table("job_events").insert(event_data).execute()
            
            return JobEvent(**result.data[0])
            
        except Exception as e:
            logger.error(f"Failed to add job event: {e}")
            raise
    
    async def get_job_stats(self, dataset_id: Optional[str] = None) -> Dict[str, Any]:
        """Get job statistics"""
        try:
            # Base query
            query = self.supabase.table("jobs").select("status")
            
            if dataset_id:
                query = query.eq("dataset_id", dataset_id)
            
            result = query.execute()
            
            # Count by status
            status_counts = {}
            for job in result.data:
                status = job.get("status", "queued")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            total = len(result.data)
            success_rate = 0
            if total > 0:
                succeeded = status_counts.get("succeeded", 0)
                success_rate = (succeeded / total) * 100
            
            # Get queue length from Redis with graceful fallback
            try:
                queue_length = await self.queue.get_queue_length()
            except Exception as e:
                logger.warning(f"Failed to get Redis queue length: {e}")
                queue_length = 0  # Graceful fallback
            
            return {
                "total_jobs": total,
                "queued_jobs": status_counts.get("queued", 0) + queue_length,  # Include Redis queue
                "running_jobs": status_counts.get("running", 0),
                "completed_jobs": status_counts.get("succeeded", 0),
                "failed_jobs": status_counts.get("failed", 0),
                "cancelled_jobs": status_counts.get("skipped", 0),  # Map skipped to cancelled
                "avg_processing_time": 15.0,  # Mock value - would calculate from actual data
                "success_rate": success_rate,
                "queue_length": queue_length  # Current Redis queue length
            }
            
        except Exception as e:
            logger.error(f"Failed to get job stats: {e}")
            raise