"""
Test cases for rate limiting middleware
"""

import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock, Mock
from fastapi import Request
from fastapi.testclient import TestClient
from app.core.rate_limit import RateLimitMiddleware


class TestRateLimitMiddleware:
    """Test rate limiting middleware functionality"""
    
    def test_path_pattern_matching(self):
        """Test URL pattern matching for rate limits"""
        middleware = RateLimitMiddleware(app=None)
        
        # Test exact matches
        assert middleware.path_matches_pattern(
            "/api/v1/datasets", 
            "/api/v1/datasets"
        ) is True
        
        # Test pattern with placeholders
        assert middleware.path_matches_pattern(
            "/api/v1/datasets/123/process-huggingface",
            "/api/v1/datasets/{dataset_id}/process-huggingface"
        ) is True
        
        assert middleware.path_matches_pattern(
            "/api/v1/datasets/abc-def/presign", 
            "/api/v1/datasets/{dataset_id}/presign"
        ) is True
        
        # Test non-matches
        assert middleware.path_matches_pattern(
            "/api/v1/datasets/123/wrong-endpoint",
            "/api/v1/datasets/{dataset_id}/process-huggingface"
        ) is False
        
        assert middleware.path_matches_pattern(
            "/api/v1/scenes/123",
            "/api/v1/datasets/{dataset_id}"
        ) is False
    
    def test_rate_limit_configuration(self):
        """Test rate limit configuration for different endpoints"""
        middleware = RateLimitMiddleware(app=None)
        
        # Test specific endpoint limits
        hf_limits = middleware.get_rate_limit_for_path("/api/v1/datasets/123/process-huggingface")
        assert hf_limits['requests'] == 5
        assert hf_limits['window'] == 300
        
        presign_limits = middleware.get_rate_limit_for_path("/api/v1/datasets/abc/presign")
        assert presign_limits['requests'] == 20
        assert presign_limits['window'] == 60
        
        # Test default limits
        default_limits = middleware.get_rate_limit_for_path("/api/v1/some/random/endpoint")
        assert default_limits['requests'] == 100
        assert default_limits['window'] == 60
    
    def test_client_identifier_extraction(self):
        """Test client IP extraction from request"""
        middleware = RateLimitMiddleware(app=None)
        
        # Mock request with forwarded headers
        request_mock = MagicMock()
        request_mock.headers.get.return_value = "192.168.1.100, 10.0.0.1"
        request_mock.client.host = "127.0.0.1"
        
        client_id = middleware.get_client_identifier(request_mock)
        assert client_id == "192.168.1.100"  # First IP from X-Forwarded-For
        
        # Mock request without forwarded headers
        request_mock.headers.get.return_value = None
        request_mock.client.host = "192.168.1.50"
        
        client_id = middleware.get_client_identifier(request_mock)
        assert client_id == "192.168.1.50"
        
        # Mock request with no client info
        request_mock.headers.get.return_value = None
        request_mock.client = None
        
        client_id = middleware.get_client_identifier(request_mock)
        assert client_id == "unknown"
    
    @pytest.mark.asyncio
    async def test_rate_limit_check_with_redis(self):
        """Test rate limit checking with Redis backend"""
        middleware = RateLimitMiddleware(app=None)
        
        # Mock Redis client and pipeline properly
        mock_redis = Mock()
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.execute = AsyncMock(return_value=[None, 5, None, None])  # 5 requests in window
        
        with patch('app.core.rate_limit.get_redis', return_value=mock_redis):
            limits = {'requests': 10, 'window': 60}
            result = await middleware.check_rate_limit("192.168.1.1", limits)
            
            assert result['allowed'] is True
            assert result['requests_made'] == 6  # 5 + current request
            assert result['requests_remaining'] == 4  # 10 - 6
            
            # Redis pipeline should be called with correct operations
            mock_pipeline.zremrangebyscore.assert_called_once()
            mock_pipeline.zcard.assert_called_once()
            mock_pipeline.zadd.assert_called_once()
            mock_pipeline.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test behavior when rate limit is exceeded"""
        middleware = RateLimitMiddleware(app=None)
        
        # Mock Redis client returning limit exceeded
        mock_redis = Mock()
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.execute = AsyncMock(return_value=[None, 10, None, None])  # 10 requests in window
        
        with patch('app.core.rate_limit.get_redis', return_value=mock_redis):
            limits = {'requests': 10, 'window': 60}
            result = await middleware.check_rate_limit("192.168.1.1", limits)
            
            assert result['allowed'] is False
            assert result['requests_made'] == 11  # 10 + current request
            assert result['requests_remaining'] == 0
    
    @pytest.mark.asyncio
    async def test_redis_unavailable_fallback(self):
        """Test fallback behavior when Redis is unavailable"""
        middleware = RateLimitMiddleware(app=None)
        
        # Mock Redis as unavailable
        with patch('app.core.rate_limit.get_redis', return_value=None):
            limits = {'requests': 10, 'window': 60}
            result = await middleware.check_rate_limit("192.168.1.1", limits)
            
            # Should allow request when Redis is unavailable
            assert result['allowed'] is True
            assert result['requests_made'] == 0
            assert result['requests_remaining'] == 10
    
    @pytest.mark.asyncio
    async def test_redis_error_handling(self):
        """Test error handling in Redis operations"""
        middleware = RateLimitMiddleware(app=None)
        
        # Mock Redis client that raises exceptions
        mock_redis = Mock()
        mock_redis.pipeline.side_effect = Exception("Redis connection error")
        
        with patch('app.core.rate_limit.get_redis', return_value=mock_redis):
            limits = {'requests': 10, 'window': 60}
            result = await middleware.check_rate_limit("192.168.1.1", limits)
            
            # Should allow request when Redis operations fail
            assert result['allowed'] is True
            assert result['requests_made'] == 0
            assert result['requests_remaining'] == 10


class TestRateLimitIntegration:
    """Integration tests for rate limiting with FastAPI"""
    
    @pytest.fixture
    def app_with_rate_limit(self):
        """Create FastAPI app with rate limiting for testing"""
        from fastapi import FastAPI
        
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, default_requests=5, default_window=60)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        @app.get("/health")  # Should be exempted from rate limiting
        async def health():
            return {"status": "ok"}
        
        return app
    
    def test_rate_limit_headers_in_response(self, app_with_rate_limit):
        """Test that rate limit headers are added to responses"""
        with patch('app.core.rate_limit.get_redis', return_value=None):  # No Redis for simplicity
            client = TestClient(app_with_rate_limit)
            response = client.get("/test")
            
            assert response.status_code == 200
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Window" in response.headers
            
            assert response.headers["X-RateLimit-Limit"] == "5"
            assert response.headers["X-RateLimit-Window"] == "60"
    
    def test_health_endpoint_exemption(self, app_with_rate_limit):
        """Test that health endpoints are exempt from rate limiting"""
        client = TestClient(app_with_rate_limit)
        
        # Health endpoint should not have rate limit headers
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response.headers