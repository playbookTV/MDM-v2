"""
Redis queue service for job processing
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.redis import get_redis, RedisQueue, RedisEventStream
from app.core.config import settings

logger = logging.getLogger(__name__)

class QueueService:
    """Service for job queue management with Redis"""
    
    def __init__(self):
        """Initialize Redis connection and queue managers"""
        self.redis = get_redis()
        self.job_queue = RedisQueue(settings.REDIS_JOB_QUEUE)
        self.event_stream = RedisEventStream(settings.REDIS_EVENT_STREAM)
    
    async def enqueue_job(self, job_id: str, job_type: str, config: Dict[str, Any]):
        """
        Enqueue a job for processing
        
        Args:
            job_id: Unique job identifier
            job_type: Type of job (dataset, scene, cleanup, etc.)
            config: Job configuration and parameters
        """
        try:
            job_data = {
                'id': job_id,
                'type': job_type,
                'config': config,
                'status': 'queued',
                'created_at': datetime.utcnow().isoformat(),
                'priority': config.get('priority', 0)
            }
            
            # Add to Redis queue
            await self.job_queue.enqueue_job(job_data)
            
            # Publish enqueue event
            await self.event_stream.publish_event(
                job_id, 
                'job_queued',
                {
                    'type': job_type,
                    'timestamp': job_data['created_at'],
                    'queue_position': await self.job_queue.get_queue_length()
                }
            )
            
            logger.info(f"✅ Job {job_id} ({job_type}) enqueued successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue job {job_id}: {e}")
            return False
    
    async def cancel_job(self, job_id: str):
        """
        Cancel a queued or running job
        
        Args:
            job_id: Job identifier to cancel
        """
        if not self.redis:
            logger.warning("Redis not available - cannot cancel job")
            return False
            
        try:
            # Mark job as cancelled in a cancellation set
            await self.redis.sadd(f"{settings.REDIS_JOB_QUEUE}:cancelled", job_id)
            
            # Publish cancellation event
            await self.event_stream.publish_event(
                job_id,
                'job_cancelled',
                {
                    'timestamp': datetime.utcnow().isoformat(),
                    'reason': 'user_request'
                }
            )
            
            logger.info(f"Job {job_id} marked for cancellation")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    async def is_job_cancelled(self, job_id: str) -> bool:
        """Check if a job has been cancelled"""
        if not self.redis:
            return False
            
        try:
            return await self.redis.sismember(f"{settings.REDIS_JOB_QUEUE}:cancelled", job_id)
        except Exception as e:
            logger.error(f"Failed to check cancellation status for job {job_id}: {e}")
            return False
    
    async def get_job_logs(self, job_id: str, since: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get job logs from Redis stream
        
        Args:
            job_id: Job identifier
            since: Timestamp to get logs since (optional)
            limit: Maximum number of log entries
            
        Returns:
            List of log/event entries for the job
        """
        try:
            events = await self.event_stream.read_events(job_id=job_id, count=limit)
            
            # Filter by timestamp if specified
            if since:
                try:
                    since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                    events = [
                        event for event in events 
                        if datetime.fromisoformat(event.get('timestamp', '').replace('Z', '+00:00')) >= since_dt
                    ]
                except ValueError:
                    logger.warning(f"Invalid timestamp format: {since}")
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get logs for job {job_id}: {e}")
            return []
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            queue_length = await self.job_queue.get_queue_length()
            
            # Get active workers (simplified - could be enhanced with worker heartbeats)
            active_workers = 0
            if self.redis:
                try:
                    # Check for recent activity in event stream
                    recent_events = await self.event_stream.read_events(count=50)
                    recent_jobs = set()
                    for event in recent_events:
                        if event.get('event_type') in ['job_started', 'progress']:
                            recent_jobs.add(event.get('job_id'))
                    active_workers = len(recent_jobs)
                except Exception:
                    pass
            
            return {
                'queue_length': queue_length,
                'active_workers': active_workers,
                'redis_available': self.redis is not None
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {
                'queue_length': 0,
                'active_workers': 0,
                'redis_available': False
            }
    
    async def get_worker_status(self) -> List[Dict[str, Any]]:
        """Get status of all workers (simplified implementation)"""
        try:
            if not self.redis:
                return []
            
            # Get recent worker activity from events
            recent_events = await self.event_stream.read_events(count=100)
            
            workers = {}
            for event in recent_events:
                job_id = event.get('job_id')
                if job_id and event.get('event_type') in ['job_started', 'progress', 'job_completed']:
                    workers[job_id] = {
                        'job_id': job_id,
                        'status': 'processing' if event.get('event_type') == 'progress' else 'idle',
                        'last_activity': event.get('timestamp'),
                        'current_stage': event.get('stage', 'unknown')
                    }
            
            return list(workers.values())
            
        except Exception as e:
            logger.error(f"Failed to get worker status: {e}")
            return []
    
    async def clear_cancelled_jobs(self):
        """Clear the cancelled jobs set (maintenance operation)"""
        if not self.redis:
            return
            
        try:
            await self.redis.delete(f"{settings.REDIS_JOB_QUEUE}:cancelled")
            logger.info("Cleared cancelled jobs set")
        except Exception as e:
            logger.error(f"Failed to clear cancelled jobs: {e}")