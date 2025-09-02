"""
Redis connection and queue management
"""

import json
import logging
import redis.asyncio as redis
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis connection pool
redis_pool: Optional[redis.ConnectionPool] = None
redis_client: Optional[redis.Redis] = None

async def init_redis() -> redis.Redis:
    """Initialize Redis connection pool and client"""
    global redis_pool, redis_client
    
    try:
        logger.info(f"Attempting to connect to Redis at: {settings.REDIS_URL}")
        
        # Create connection pool with timeout settings
        redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            encoding='utf-8',
            decode_responses=True,
            max_connections=20,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        
        # Create Redis client
        redis_client = redis.Redis(connection_pool=redis_pool)
        
        # Test connection
        await redis_client.ping()
        
        logger.info("✅ Redis connection established successfully")
        return redis_client
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        logger.warning("Continuing without Redis - job queue features will be disabled")
        
        # Create mock Redis client for development
        redis_client = None
        return None

async def close_redis():
    """Close Redis connection"""
    global redis_pool, redis_client
    
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")
    
    if redis_pool:
        await redis_pool.disconnect()
        logger.info("Redis pool disconnected")

def get_redis() -> Optional[redis.Redis]:
    """Get Redis client instance"""
    return redis_client

class RedisQueue:
    """Redis-based job queue manager"""
    
    def __init__(self, queue_name: str = None):
        self.queue_name = queue_name or settings.REDIS_JOB_QUEUE
    
    def _get_redis(self):
        """Get Redis client instance dynamically"""
        return get_redis()
    
    async def enqueue_job(self, job_data: dict) -> str:
        """Add job to queue"""
        redis = self._get_redis()
        if not redis:
            logger.warning("Redis not available - skipping job queue")
            return job_data.get('id', 'unknown')
            
        try:
            # Use Redis list for FIFO queue, properly serialize JSON
            job_json = json.dumps(job_data)
            await redis.lpush(self.queue_name, job_json)
            logger.info(f"Job enqueued to {self.queue_name}: {job_data.get('id')}")
            return job_data.get('id', 'unknown')
        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            return job_data.get('id', 'unknown')
    
    async def dequeue_job(self, timeout: int = 10) -> Optional[dict]:
        """Get job from queue with blocking pop"""
        redis = self._get_redis()
        if not redis:
            return None
            
        try:
            # Use blocking right pop for FIFO processing
            result = await redis.brpop(self.queue_name, timeout=timeout)
            if result:
                queue_name, job_json = result
                # Parse job data from JSON
                return json.loads(job_json)
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue job: {e}")
            return None
    
    async def get_queue_length(self) -> int:
        """Get current queue length"""
        redis = self._get_redis()
        if not redis:
            return 0
            
        try:
            return await redis.llen(self.queue_name)
        except Exception as e:
            logger.error(f"Failed to get queue length: {e}")
            return 0

class RedisEventStream:
    """Redis streams for job events and monitoring"""
    
    def __init__(self, stream_name: str = None):
        self.stream_name = stream_name or settings.REDIS_EVENT_STREAM
    
    def _get_redis(self):
        """Get Redis client instance dynamically"""
        return get_redis()
    
    async def publish_event(self, job_id: str, event_type: str, data: dict) -> str:
        """Publish job event to stream"""
        redis = self._get_redis()
        if not redis:
            logger.debug("Redis not available - skipping event publishing")
            return f"mock-{job_id}-{event_type}"
            
        try:
            event_data = {
                'job_id': job_id,
                'event_type': event_type,
                'timestamp': str(data.get('timestamp', '')),
                **data
            }
            
            # Add to Redis stream
            message_id = await redis.xadd(self.stream_name, event_data)
            logger.debug(f"Event published to {self.stream_name}: {event_type} for job {job_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return f"error-{job_id}-{event_type}"
    
    async def read_events(self, job_id: str = None, count: int = 100) -> list:
        """Read events from stream"""
        redis = self._get_redis()
        if not redis:
            return []
            
        try:
            # Read from stream
            messages = await redis.xread({self.stream_name: '0'}, count=count)
            
            events = []
            for stream_name, stream_messages in messages:
                for message_id, fields in stream_messages:
                    if not job_id or fields.get('job_id') == job_id:
                        events.append({
                            'id': message_id,
                            **fields
                        })
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to read events: {e}")
            return []