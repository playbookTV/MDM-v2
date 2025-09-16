#!/usr/bin/env python3

"""
Modomo Dataset Management API Server
FastAPI backend for React web application
"""

import uvicorn
import logging
import sentry_sdk
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.api.routes import (
    datasets_new as datasets,
    jobs_new as jobs,
    scenes_new as scenes,
    reviews_new as reviews,
    stats_new as stats,
    queue,
    images,
    test_sentry
)
from app.core.config import settings
from app.core.supabase import init_supabase
from app.core.redis import init_redis, close_redis
from app.core.logging import setup_logging
from app.core.rate_limit import RateLimitMiddleware

# Setup logging
setup_logging()

def _enhance_sentry_event(event, hint):
    """Enhance Sentry events with custom tags and context"""
    # Add custom tags
    event.setdefault("tags", {}).update({
        "service": "modomo-api",
        "component": "dataset-management"
    })
    
    # Add extra context for job processing errors
    if "exception" in event:
        exc = hint.get("exc_info")
        if exc and "job" in str(exc[1]).lower():
            event.setdefault("extra", {})["job_context"] = True
    
    # Filter out health check spam in production
    if settings.PRODUCTION and event.get("request", {}).get("url", "").endswith("/health"):
        return None
        
    return event

# Initialize Sentry with enhanced configuration
sentry_sdk.init(
    dsn="https://33f7bb870c7155ef9a03c9757c9e5b3b@o4508932213637120.ingest.de.sentry.io/4510024361771088",
    integrations=[
        FastApiIntegration(transaction_style="endpoint"),
        LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
    ],
    # Enhanced performance monitoring
    traces_sample_rate=1.0,  # Capture 100% of transactions for development
    profile_session_sample_rate=1.0,  # Profile 100% of sessions
    profile_lifecycle="trace",  # Auto-profile during transactions
    
    # Enhanced data collection
    send_default_pii=True,  # Include request headers and IP for users
    enable_logs=True,  # Send logs to Sentry
    
    # Environment and release info
    environment=settings.ENVIRONMENT,
    release=f"modomo-api@{settings.VERSION}",
    
    # Custom tags for better filtering
    before_send=lambda event, hint: _enhance_sentry_event(event, hint),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Modomo Dataset Management API...")

    # Initialize Supabase connection
    await init_supabase()
    print("✅ Supabase initialized")

    # Initialize Redis connection for job queue
    await init_redis()
    print("✅ Redis initialized")

    print("✅ Application started successfully")

    yield

    # Shutdown
    print("🛑 Shutting down Modomo API...")
    await close_redis()

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Modomo Dataset Management API",
        version="1.0.0",
        description="""
## Overview

The Modomo Dataset Management API provides comprehensive endpoints for AI-powered interior design dataset curation, processing, and review.

### Key Features
- 🎯 **Dataset Management**: Import datasets from local files or HuggingFace
- 🤖 **AI Processing Pipeline**: Scene classification, object detection, segmentation, depth estimation
- 👁️ **Human Review**: Approve/reject/edit detected objects and scenes
- 📊 **Analytics**: Real-time statistics and distribution metrics
- 💾 **Storage**: Cloudflare R2 for assets, Supabase for metadata

### Authentication
Currently uses API key authentication for internal use. Contact admin for access.

### Rate Limiting
- Standard: 100 requests per minute
- Bulk operations: 10 requests per minute

### Response Format
All endpoints return JSON with consistent error handling:
```json
{
  "data": {...},
  "error": null,
  "meta": {
    "timestamp": "2024-01-15T12:00:00Z",
    "version": "1.0.0"
  }
}
```
        """,
        routes=app.routes,
        tags=[
            {
                "name": "datasets",
                "description": "Dataset management operations",
                "externalDocs": {
                    "description": "Dataset documentation",
                    "url": "https://docs.modomo.ai/datasets"
                }
            },
            {
                "name": "jobs",
                "description": "Processing job management",
                "externalDocs": {
                    "description": "Job processing guide",
                    "url": "https://docs.modomo.ai/jobs"
                }
            },
            {
                "name": "scenes",
                "description": "Scene analysis and management"
            },
            {
                "name": "reviews",
                "description": "Human review operations"
            },
            {
                "name": "stats",
                "description": "Analytics and statistics"
            },
            {
                "name": "queue",
                "description": "Job queue monitoring"
            },
            {
                "name": "images",
                "description": "Image upload and management"
            }
        ]
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://modomo.ai/logo.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Create FastAPI app
app = FastAPI(
    title="Modomo Dataset Management API",
    description="Backend API for AI-powered interior design dataset curation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_url="/openapi.json"
)

app.openapi = custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Setup Prometheus metrics
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="modomo_inprogress",
    inprogress_labels=True,
)

instrumentator.instrument(app).expose(app, include_in_schema=False)

# Add custom metrics
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, REGISTRY
import sys

# Only create metrics once (avoid duplicates on reload)
if 'modomo_metrics_initialized' not in sys.modules:
    # Custom metrics
    dataset_imports = Counter('modomo_dataset_imports_total', 'Total number of dataset imports', ['source'])
    job_processing_time = Histogram('modomo_job_processing_seconds', 'Job processing time in seconds', ['job_type'])
    active_jobs = Gauge('modomo_active_jobs', 'Number of active processing jobs')
    scene_reviews = Counter('modomo_scene_reviews_total', 'Total number of scene reviews', ['verdict'])
    
    # Mark as initialized
    sys.modules['modomo_metrics_initialized'] = True
else:
    # Metrics already exist, get them from registry
    for collector in REGISTRY._collector_to_names:
        if hasattr(collector, '_name'):
            if collector._name == 'modomo_dataset_imports_total':
                dataset_imports = collector
            elif collector._name == 'modomo_job_processing_seconds':
                job_processing_time = collector
            elif collector._name == 'modomo_active_jobs':
                active_jobs = collector
            elif collector._name == 'modomo_scene_reviews_total':
                scene_reviews = collector

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway deployment"""
    return {"ok": True, "status": "healthy", "service": "modomo-api"}

# Mount API routes
app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(scenes.router, prefix="/api/v1/scenes", tags=["scenes"])
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["reviews"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["stats"])
app.include_router(queue.router, prefix="/api/v1/queue", tags=["queue"])
app.include_router(images.router, prefix="/api/v1/images", tags=["images"])

# Test routes (only in development)
if not settings.PRODUCTION:
    app.include_router(test_sentry.router, prefix="/api/v1/test", tags=["testing"])

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error", 
                "message": "Internal server error",
                "status_code": 500
            }
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=False,  # Disabled to prevent Prometheus metric duplication
        log_level="info"
    )