#!/usr/bin/env python3

"""
Modomo Dataset Management API Server
FastAPI backend for React web application
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from contextlib import asynccontextmanager

from app.api.routes import datasets_new as datasets, jobs, scenes, reviews, stats
from app.core.config import settings
from app.core.supabase import init_supabase
from app.core.logging import setup_logging

# Setup logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Modomo Dataset Management API...")
    
    # Initialize Supabase connection
    await init_supabase()
    print("✅ Supabase initialized")
    
    # TODO: Initialize Redis connection for job queue
    print("✅ Application started successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Modomo API...")

# Create FastAPI app
app = FastAPI(
    title="Modomo Dataset Management API",
    description="Backend API for AI-powered interior design dataset curation",
    version="1.0.0",
    docs_url="/docs" if not settings.PRODUCTION else None,
    redoc_url="/redoc" if not settings.PRODUCTION else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        reload=not settings.PRODUCTION,
        log_level="info"
    )