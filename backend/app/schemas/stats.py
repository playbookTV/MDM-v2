"""
Statistics-related Pydantic schemas  
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# System health
class SystemHealth(BaseModel):
    """System health status"""
    status: str = Field(..., description="Overall system status")
    database_status: str = Field(..., description="Database connection status")
    storage_status: str = Field(..., description="Storage service status")
    queue_status: str = Field(..., description="Job queue status")
    uptime_seconds: int = Field(..., description="System uptime in seconds")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")

# Processing metrics
class ProcessingMetrics(BaseModel):
    """Processing performance metrics"""
    total_scenes_processed: int = Field(..., description="Total scenes processed")
    avg_processing_time_seconds: float = Field(..., description="Average processing time")
    scenes_per_hour: float = Field(..., description="Scenes processed per hour")
    success_rate_percent: float = Field(..., description="Processing success rate")
    error_rate_percent: float = Field(..., description="Processing error rate")
    queue_length: int = Field(..., description="Current queue length")

# Model performance
class ModelPerformanceMetrics(BaseModel):
    """AI model performance metrics"""
    model_name: str = Field(..., description="Model name")
    avg_confidence: float = Field(..., description="Average confidence score")
    predictions_count: int = Field(..., description="Total predictions made")
    high_confidence_rate: float = Field(..., description="Rate of high confidence predictions")
    low_confidence_rate: float = Field(..., description="Rate of low confidence predictions")

# Dataset statistics  
class DatasetStats(BaseModel):
    """Dataset statistics"""
    dataset_id: str = Field(..., description="Dataset ID")
    dataset_name: str = Field(..., description="Dataset name")
    total_scenes: int = Field(..., description="Total scenes")
    processed_scenes: int = Field(..., description="Processed scenes")
    total_objects: int = Field(..., description="Total objects detected")
    avg_objects_per_scene: float = Field(..., description="Average objects per scene")
    completion_rate: float = Field(..., description="Processing completion rate")

# Trends
class ProcessingTrend(BaseModel):
    """Processing trend data point"""
    timestamp: datetime = Field(..., description="Data point timestamp")
    scenes_processed: int = Field(..., description="Scenes processed")
    avg_processing_time: float = Field(..., description="Average processing time")
    success_rate: float = Field(..., description="Success rate")

class SystemMetricsTrend(BaseModel):
    """System metrics trend data point"""
    timestamp: datetime = Field(..., description="Data point timestamp")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage MB")
    queue_length: int = Field(..., description="Queue length")
    active_jobs: int = Field(..., description="Active jobs count")

# Error analysis
class ErrorAnalysis(BaseModel):
    """Error analysis data"""
    error_type: str = Field(..., description="Type of error")
    count: int = Field(..., description="Error occurrence count")
    rate: float = Field(..., description="Error rate percentage")
    last_occurrence: Optional[datetime] = Field(None, description="Last error occurrence")

# Top performing datasets
class TopPerformingDatasets(BaseModel):
    """Top performing dataset metrics"""
    dataset_id: str = Field(..., description="Dataset ID")
    dataset_name: str = Field(..., description="Dataset name")
    total_scenes: int = Field(..., description="Total scenes")
    avg_confidence: float = Field(..., description="Average AI confidence")
    success_rate: float = Field(..., description="Processing success rate")
    processing_speed: float = Field(..., description="Processing speed (scenes/hour)")

# Dashboard summary
class DashboardSummary(BaseModel):
    """Dashboard summary statistics"""
    total_datasets: int = Field(..., description="Total datasets")
    total_scenes: int = Field(..., description="Total scenes")
    total_objects: int = Field(..., description="Total objects")
    scenes_processed_today: int = Field(..., description="Scenes processed today")
    active_jobs: int = Field(..., description="Active jobs")
    avg_confidence: float = Field(..., description="Overall average confidence")
    system_health_score: float = Field(..., description="System health score (0-100)")
    recent_activity: List[Dict[str, Any]] = Field(..., description="Recent system activity")