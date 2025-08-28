"""
Rate limiting middleware using Redis
"""

import time
import logging
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.redis import get_redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware that tracks requests per IP address using Redis.
    
    Default limits:
    - 100 requests per minute for general endpoints
    - 10 requests per minute for expensive operations (dataset processing, uploads)
    """
    
    def __init__(self, app, default_requests: int = 100, default_window: int = 60):
        super().__init__(app)
        self.default_requests = default_requests
        self.default_window = default_window
        
        # Specific rate limits for different endpoint patterns
        self.endpoint_limits = {
            '/api/v1/datasets/{dataset_id}/process-huggingface': {'requests': 5, 'window': 300},  # 5 per 5 minutes
            '/api/v1/datasets/{dataset_id}/presign': {'requests': 20, 'window': 60},  # 20 per minute
            '/api/v1/datasets': {'requests': 30, 'window': 60},  # 30 per minute for dataset operations
        }
    
    def get_rate_limit_for_path(self, path: str) -> Dict[str, int]:
        """Get rate limit configuration for a specific path"""
        
        # Check for exact matches first
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # Check for pattern matches
        for pattern, limits in self.endpoint_limits.items():
            if self.path_matches_pattern(path, pattern):
                return limits
        
        # Return default limits
        return {'requests': self.default_requests, 'window': self.default_window}
    
    def path_matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches a pattern with placeholders like {dataset_id}"""
        path_parts = path.strip('/').split('/')
        pattern_parts = pattern.strip('/').split('/')
        
        if len(path_parts) != len(pattern_parts):
            return False
        
        for path_part, pattern_part in zip(path_parts, pattern_parts):
            # Skip placeholder parts (e.g., {dataset_id})
            if pattern_part.startswith('{') and pattern_part.endswith('}'):
                continue
            # Exact match required for non-placeholder parts
            if path_part != pattern_part:
                return False
        
        return True
    
    def get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting (IP address)"""
        # Try to get real IP from headers (for reverse proxies)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Take the first IP in case of multiple proxies
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.client.host if request.client else 'unknown'
        
        return client_ip
    
    async def check_rate_limit(self, client_id: str, limits: Dict[str, int]) -> Dict[str, any]:
        """
        Check if client has exceeded rate limit using sliding window in Redis
        
        Returns:
            Dict with 'allowed' (bool), 'requests_made' (int), 'requests_remaining' (int)
        """
        redis_client = get_redis()
        if not redis_client:
            # If Redis is not available, allow the request but log warning
            logger.warning("Redis not available for rate limiting - allowing request")
            return {
                'allowed': True,
                'requests_made': 0,
                'requests_remaining': limits['requests']
            }
        
        requests_limit = limits['requests']
        window_seconds = limits['window']
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        # Redis key for this client's rate limit data
        key = f"rate_limit:{client_id}"
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = redis_client.pipeline()
            
            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in the window
            pipe.zcard(key)
            
            # Add current request timestamp
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration for cleanup
            pipe.expire(key, window_seconds + 1)
            
            results = await pipe.execute()
            requests_made = results[1]  # Count from zcard
            
            allowed = requests_made < requests_limit
            requests_remaining = max(0, requests_limit - requests_made - 1)  # -1 for current request
            
            return {
                'allowed': allowed,
                'requests_made': requests_made + 1,  # Include current request
                'requests_remaining': requests_remaining
            }
            
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            # Allow request if Redis operations fail
            return {
                'allowed': True,
                'requests_made': 0,
                'requests_remaining': requests_limit
            }
    
    async def dispatch(self, request: Request, call_next):
        """Process rate limiting for incoming requests"""
        
        # Skip rate limiting for health checks and static files
        if request.url.path in ['/health', '/docs', '/redoc', '/openapi.json']:
            return await call_next(request)
        
        # Get client identifier
        client_id = self.get_client_identifier(request)
        
        # Get rate limits for this endpoint
        limits = self.get_rate_limit_for_path(request.url.path)
        
        # Check rate limit
        result = await self.check_rate_limit(client_id, limits)
        
        if not result['allowed']:
            # Rate limit exceeded
            logger.warning(
                f"Rate limit exceeded for {client_id} on {request.url.path}: "
                f"{result['requests_made']}/{limits['requests']} requests in {limits['window']}s"
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {limits['window']} seconds.",
                headers={
                    "X-RateLimit-Limit": str(limits['requests']),
                    "X-RateLimit-Remaining": str(result['requests_remaining']),
                    "X-RateLimit-Window": str(limits['window']),
                    "Retry-After": str(limits['window'])
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limits['requests'])
        response.headers["X-RateLimit-Remaining"] = str(result['requests_remaining'])
        response.headers["X-RateLimit-Window"] = str(limits['window'])
        
        return response