"""
Statistics and analytics endpoints using Supabase
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.stats import StatsService

logger = logging.getLogger(__name__)
router = APIRouter()

# Response schemas to match React expectations
class SystemHealth(BaseModel):
    status: str
    database_status: str
    storage_status: str
    queue_status: str
    uptime_seconds: int
    memory_usage_mb: float
    cpu_usage_percent: float

class ProcessingMetrics(BaseModel):
    total_scenes_processed: int
    avg_processing_time_seconds: float
    scenes_per_hour: float
    success_rate_percent: float
    error_rate_percent: float
    queue_length: int

class ModelPerformanceMetrics(BaseModel):
    model_name: str
    avg_confidence: float
    predictions_count: int
    high_confidence_rate: float
    low_confidence_rate: float

class DatasetStats(BaseModel):
    dataset_id: str
    dataset_name: str
    total_scenes: int
    processed_scenes: int
    total_objects: int
    avg_objects_per_scene: float
    completion_rate: float

class ProcessingTrend(BaseModel):
    timestamp: str
    scenes_processed: int
    avg_processing_time: float
    success_rate: float

class SystemMetricsTrend(BaseModel):
    timestamp: str
    cpu_usage: float
    memory_usage: float
    queue_length: int
    active_jobs: int

class DashboardSummary(BaseModel):
    total_datasets: int
    total_scenes: int
    total_objects: int
    scenes_processed_today: int
    active_jobs: int
    avg_confidence: float
    system_health_score: float
    recent_activity: List[Dict[str, Any]]

@router.get("/health", response_model=SystemHealth)
async def get_system_health():
    """Get system health metrics"""
    try:
        service = StatsService()
        health = await service.get_system_health()
        
        return SystemHealth(**health)
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        # Return basic unhealthy status on error
        return SystemHealth(
            status="unhealthy",
            database_status="error",
            storage_status="unknown",
            queue_status="unknown",
            uptime_seconds=0,
            memory_usage_mb=0,
            cpu_usage_percent=0
        )

@router.get("/processing-metrics", response_model=ProcessingMetrics)
async def get_processing_metrics(
    hours: int = Query(24, description="Time window in hours")
):
    """Get processing performance metrics"""
    try:
        service = StatsService()
        metrics = await service.get_processing_metrics(hours)
        
        return ProcessingMetrics(**metrics)
        
    except Exception as e:
        logger.error(f"Failed to get processing metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing metrics")

@router.get("/model-performance", response_model=List[ModelPerformanceMetrics])
async def get_model_performance(
    hours: int = Query(24, description="Time window in hours")
):
    """Get AI model performance metrics"""
    try:
        service = StatsService()
        performance = await service.get_model_performance(hours)
        
        return [ModelPerformanceMetrics(**model) for model in performance]
        
    except Exception as e:
        logger.error(f"Failed to get model performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model performance")

@router.get("/dataset-stats", response_model=List[DatasetStats])
async def get_dataset_stats():
    """Get per-dataset statistics"""
    try:
        service = StatsService()
        stats = await service.get_dataset_stats()
        
        return [DatasetStats(**dataset) for dataset in stats]
        
    except Exception as e:
        logger.error(f"Failed to get dataset stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dataset stats")

@router.get("/processing-trends", response_model=List[ProcessingTrend])
async def get_processing_trends(
    hours: int = Query(24, description="Time window in hours"),
    interval: int = Query(1, description="Interval in hours")
):
    """Get processing trend data"""
    try:
        service = StatsService()
        trends = await service.get_processing_trends(hours, interval)
        
        return [ProcessingTrend(**trend) for trend in trends]
        
    except Exception as e:
        logger.error(f"Failed to get processing trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing trends")

@router.get("/system-trends", response_model=List[SystemMetricsTrend])
async def get_system_trends(
    hours: int = Query(24, description="Time window in hours"),
    interval: int = Query(1, description="Interval in hours")
):
    """Get system metrics trend data"""
    try:
        service = StatsService()
        trends = await service.get_system_trends(hours, interval)
        
        return [SystemMetricsTrend(**trend) for trend in trends]
        
    except Exception as e:
        logger.error(f"Failed to get system trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system trends")

@router.get("/dashboard-summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    """Get dashboard summary statistics"""
    try:
        service = StatsService()
        summary = await service.get_dashboard_summary()
        
        return DashboardSummary(**summary)
        
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard summary")

# Additional endpoints for specific React hook compatibility
@router.get("/overview")
async def get_stats_overview():
    """Get general stats overview (compatible with useStats hook)"""
    try:
        service = StatsService()
        
        # Get summary data
        summary = await service.get_dashboard_summary()
        health = await service.get_system_health()
        
        return {
            "total_datasets": summary["total_datasets"],
            "total_scenes": summary["total_scenes"],
            "total_objects": summary["total_objects"],
            "system_status": health["status"],
            "avg_confidence": summary["avg_confidence"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats overview")

@router.get("/distribution/{kind}")
async def get_stats_distribution(kind: str):
    """Get distribution statistics for a specific category"""
    try:
        service = StatsService()
        
        # Mock distribution data - in production would query actual distributions
        if kind == "scene_types":
            return [
                {"category": "bedroom", "count": 150},
                {"category": "living_room", "count": 120},
                {"category": "kitchen", "count": 80},
                {"category": "bathroom", "count": 60}
            ]
        elif kind == "object_categories":
            return [
                {"category": "sofa", "count": 200},
                {"category": "table", "count": 180},
                {"category": "chair", "count": 150},
                {"category": "bed", "count": 100}
            ]
        else:
            return []
        
    except Exception as e:
        logger.error(f"Failed to get {kind} distribution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get {kind} distribution")