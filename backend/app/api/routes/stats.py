"""
Statistics and analytics endpoints
"""

import logging
import psutil
import time
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.dataset import Dataset, Scene, SceneObject, Job
from app.schemas.stats import (
    SystemHealth,
    ProcessingMetrics,
    ModelPerformanceMetrics,
    DatasetStats,
    ProcessingTrend,
    SystemMetricsTrend,
    ErrorAnalysis,
    TopPerformingDatasets,
    DashboardSummary
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Track app start time for uptime calculation
APP_START_TIME = time.time()

@router.get("/health", response_model=SystemHealth)
async def get_system_health(db: AsyncSession = Depends(get_db)):
    """Get system health metrics"""
    try:
        # Test database connectivity
        await db.execute("SELECT 1")
        db_status = "healthy"
        
        # Get system metrics
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        uptime = int(time.time() - APP_START_TIME)
        
        return SystemHealth(
            status="healthy",
            database_status=db_status,
            storage_status="healthy",  # TODO: Test R2 connectivity
            queue_status="healthy",    # TODO: Test Redis connectivity
            uptime_seconds=uptime,
            memory_usage_mb=memory_info.used / (1024 * 1024),
            cpu_usage_percent=cpu_percent
        )
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
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
    db: AsyncSession = Depends(get_db),
    hours: int = Query(24, description="Time window in hours")
):
    """Get processing performance metrics"""
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Get processing stats
        processed_scenes = await db.scalar(
            select(func.count(Scene.id)).where(
                and_(
                    Scene.status == 'completed',
                    Scene.processed_at >= since
                )
            )
        )
        
        total_jobs = await db.scalar(
            select(func.count(Job.id)).where(Job.created_at >= since)
        )
        
        completed_jobs = await db.scalar(
            select(func.count(Job.id)).where(
                and_(
                    Job.status == 'completed',
                    Job.created_at >= since
                )
            )
        )
        
        # Calculate metrics
        success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        error_rate = 100 - success_rate
        scenes_per_hour = processed_scenes / hours if hours > 0 else 0
        
        return ProcessingMetrics(
            total_scenes_processed=processed_scenes or 0,
            avg_processing_time_seconds=15.0,  # Mock value
            scenes_per_hour=scenes_per_hour,
            success_rate_percent=success_rate,
            error_rate_percent=error_rate,
            queue_length=0  # TODO: Get from Redis
        )
        
    except Exception as e:
        logger.error(f"Failed to get processing metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing metrics")

@router.get("/model-performance", response_model=List[ModelPerformanceMetrics])
async def get_model_performance(
    db: AsyncSession = Depends(get_db),
    hours: int = Query(24, description="Time window in hours")
):
    """Get AI model performance metrics"""
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Scene classification performance
        scene_stats = await db.execute(
            select(
                func.avg(Scene.scene_conf).label('avg_conf'),
                func.count(Scene.id).label('count'),
                func.sum(func.case((Scene.scene_conf >= 0.8, 1), else_=0)).label('high_conf'),
                func.sum(func.case((Scene.scene_conf < 0.5, 1), else_=0)).label('low_conf')
            ).where(
                and_(
                    Scene.processed_at >= since,
                    Scene.scene_conf.is_not(None)
                )
            )
        )
        
        scene_row = scene_stats.first()
        scene_count = scene_row.count or 0
        scene_high_conf_rate = (scene_row.high_conf / scene_count * 100) if scene_count > 0 else 0
        scene_low_conf_rate = (scene_row.low_conf / scene_count * 100) if scene_count > 0 else 0
        
        # Object detection performance  
        object_stats = await db.execute(
            select(
                func.avg(SceneObject.confidence).label('avg_conf'),
                func.count(SceneObject.id).label('count'),
                func.sum(func.case((SceneObject.confidence >= 0.8, 1), else_=0)).label('high_conf'),
                func.sum(func.case((SceneObject.confidence < 0.5, 1), else_=0)).label('low_conf')
            ).where(SceneObject.created_at >= since)
        )
        
        object_row = object_stats.first()
        object_count = object_row.count or 0
        object_high_conf_rate = (object_row.high_conf / object_count * 100) if object_count > 0 else 0
        object_low_conf_rate = (object_row.low_conf / object_count * 100) if object_count > 0 else 0
        
        return [
            ModelPerformanceMetrics(
                model_name="Scene Classifier",
                avg_confidence=scene_row.avg_conf or 0,
                predictions_count=scene_count,
                high_confidence_rate=scene_high_conf_rate,
                low_confidence_rate=scene_low_conf_rate
            ),
            ModelPerformanceMetrics(
                model_name="Object Detector",
                avg_confidence=object_row.avg_conf or 0,
                predictions_count=object_count,
                high_confidence_rate=object_high_conf_rate,
                low_confidence_rate=object_low_conf_rate
            )
        ]
        
    except Exception as e:
        logger.error(f"Failed to get model performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model performance")

@router.get("/dataset-stats", response_model=List[DatasetStats])
async def get_dataset_stats(db: AsyncSession = Depends(get_db)):
    """Get per-dataset statistics"""
    try:
        query = select(
            Dataset.id,
            Dataset.name,
            Dataset.total_scenes,
            Dataset.processed_scenes,
            Dataset.total_objects,
            func.coalesce(Dataset.total_objects / Dataset.total_scenes, 0).label('avg_objects')
        ).where(Dataset.total_scenes > 0)
        
        result = await db.execute(query)
        
        stats = []
        for row in result:
            completion_rate = (row.processed_scenes / row.total_scenes * 100) if row.total_scenes > 0 else 0
            
            stats.append(DatasetStats(
                dataset_id=row.id,
                dataset_name=row.name,
                total_scenes=row.total_scenes,
                processed_scenes=row.processed_scenes,
                total_objects=row.total_objects,
                avg_objects_per_scene=row.avg_objects,
                completion_rate=completion_rate
            ))
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get dataset stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dataset stats")

@router.get("/processing-trends", response_model=List[ProcessingTrend])
async def get_processing_trends(
    db: AsyncSession = Depends(get_db),
    hours: int = Query(24, description="Time window in hours"),
    interval: int = Query(1, description="Interval in hours")
):
    """Get processing trend data"""
    try:
        # Generate mock trend data for now
        # In production, this would aggregate real metrics by time intervals
        trends = []
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        for i in range(0, hours, interval):
            timestamp = start_time + timedelta(hours=i)
            trends.append(ProcessingTrend(
                timestamp=timestamp,
                scenes_processed=max(0, 10 + i - 5),  # Mock trending data
                avg_processing_time=15.0 + (i % 3) * 2,  # Mock varying processing time
                success_rate=95.0 + (i % 5) * 1  # Mock success rate
            ))
        
        return trends
        
    except Exception as e:
        logger.error(f"Failed to get processing trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing trends")

@router.get("/dashboard-summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Get dashboard summary statistics"""
    try:
        # Get basic counts
        total_datasets = await db.scalar(select(func.count(Dataset.id)))
        total_scenes = await db.scalar(select(func.count(Scene.id)))
        total_objects = await db.scalar(select(func.count(SceneObject.id)))
        
        # Scenes processed today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        scenes_today = await db.scalar(
            select(func.count(Scene.id)).where(
                and_(
                    Scene.processed_at >= today_start,
                    Scene.status == 'completed'
                )
            )
        )
        
        # Active jobs
        active_jobs = await db.scalar(
            select(func.count(Job.id)).where(Job.status.in_(['queued', 'running']))
        )
        
        # Average confidence (scenes and objects combined)
        avg_scene_conf = await db.scalar(
            select(func.avg(Scene.scene_conf)).where(Scene.scene_conf.is_not(None))
        ) or 0
        
        avg_object_conf = await db.scalar(
            select(func.avg(SceneObject.confidence))
        ) or 0
        
        overall_avg_conf = (avg_scene_conf + avg_object_conf) / 2
        
        # Recent activity (simplified)
        recent_activity = [
            {"type": "dataset_created", "message": "New dataset uploaded", "timestamp": datetime.utcnow()},
            {"type": "job_completed", "message": "Processing job completed", "timestamp": datetime.utcnow() - timedelta(minutes=15)}
        ]
        
        return DashboardSummary(
            total_datasets=total_datasets or 0,
            total_scenes=total_scenes or 0,
            total_objects=total_objects or 0,
            scenes_processed_today=scenes_today or 0,
            active_jobs=active_jobs or 0,
            avg_confidence=overall_avg_conf,
            system_health_score=95.0,  # Mock health score
            recent_activity=recent_activity
        )
        
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard summary")