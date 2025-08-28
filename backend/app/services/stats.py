"""
Statistics service using Supabase client
"""

import logging
import psutil
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.supabase import get_supabase

logger = logging.getLogger(__name__)

# Track app start time for uptime calculation
APP_START_TIME = time.time()

class StatsService:
    """Service for statistics operations"""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            # Test database connectivity
            result = self.supabase.table("datasets").select("count").execute()
            db_status = "healthy" if result else "error"
            
            # Get system metrics
            memory_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
            uptime = int(time.time() - APP_START_TIME)
            
            return {
                "status": "healthy" if db_status == "healthy" else "unhealthy",
                "database_status": db_status,
                "storage_status": "healthy",  # TODO: Test R2 connectivity
                "queue_status": "healthy",    # TODO: Test Redis connectivity
                "uptime_seconds": uptime,
                "memory_usage_mb": memory_info.used / (1024 * 1024),
                "cpu_usage_percent": cpu_percent
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                "status": "unhealthy",
                "database_status": "error",
                "storage_status": "unknown",
                "queue_status": "unknown",
                "uptime_seconds": 0,
                "memory_usage_mb": 0,
                "cpu_usage_percent": 0
            }
    
    async def get_processing_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get processing performance metrics"""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            # Get processed scenes count
            scenes_result = (
                self.supabase.table("scenes")
                .select("id")
                .eq("status", "processed")
                .gte("created_at", since.isoformat())
                .execute()
            )
            processed_scenes = len(scenes_result.data)
            
            # Get job stats
            jobs_result = (
                self.supabase.table("jobs")
                .select("status")
                .gte("created_at", since.isoformat())
                .execute()
            )
            
            total_jobs = len(jobs_result.data)
            completed_jobs = sum(1 for job in jobs_result.data if job["status"] == "succeeded")
            
            # Calculate metrics
            success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
            error_rate = 100 - success_rate
            scenes_per_hour = processed_scenes / hours if hours > 0 else 0
            
            return {
                "total_scenes_processed": processed_scenes,
                "avg_processing_time_seconds": 15.0,  # Mock value
                "scenes_per_hour": scenes_per_hour,
                "success_rate_percent": success_rate,
                "error_rate_percent": error_rate,
                "queue_length": 0  # TODO: Get from Redis
            }
            
        except Exception as e:
            logger.error(f"Failed to get processing metrics: {e}")
            raise
    
    async def get_model_performance(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get AI model performance metrics"""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            # Scene classification performance
            scenes_result = (
                self.supabase.table("scenes")
                .select("scene_conf")
                .is_not("scene_conf", "null")
                .gte("created_at", since.isoformat())
                .execute()
            )
            
            scene_confs = [s["scene_conf"] for s in scenes_result.data]
            scene_count = len(scene_confs)
            scene_avg_conf = sum(scene_confs) / scene_count if scene_count > 0 else 0
            scene_high_conf = sum(1 for c in scene_confs if c >= 0.8)
            scene_low_conf = sum(1 for c in scene_confs if c < 0.5)
            
            # Object detection performance
            objects_result = (
                self.supabase.table("objects")
                .select("confidence")
                .gte("created_at", since.isoformat())
                .execute()
            )
            
            object_confs = [o["confidence"] for o in objects_result.data]
            object_count = len(object_confs)
            object_avg_conf = sum(object_confs) / object_count if object_count > 0 else 0
            object_high_conf = sum(1 for c in object_confs if c >= 0.8)
            object_low_conf = sum(1 for c in object_confs if c < 0.5)
            
            return [
                {
                    "model_name": "Scene Classifier",
                    "avg_confidence": scene_avg_conf,
                    "predictions_count": scene_count,
                    "high_confidence_rate": (scene_high_conf / scene_count * 100) if scene_count > 0 else 0,
                    "low_confidence_rate": (scene_low_conf / scene_count * 100) if scene_count > 0 else 0
                },
                {
                    "model_name": "Object Detector",
                    "avg_confidence": object_avg_conf,
                    "predictions_count": object_count,
                    "high_confidence_rate": (object_high_conf / object_count * 100) if object_count > 0 else 0,
                    "low_confidence_rate": (object_low_conf / object_count * 100) if object_count > 0 else 0
                }
            ]
            
        except Exception as e:
            logger.error(f"Failed to get model performance: {e}")
            raise
    
    async def get_dataset_stats(self) -> List[Dict[str, Any]]:
        """Get per-dataset statistics"""
        try:
            # Get datasets with scene counts
            datasets_result = self.supabase.table("datasets").select("*").execute()
            
            stats = []
            for dataset in datasets_result.data:
                dataset_id = dataset["id"]
                
                # Get scene count
                scenes_result = (
                    self.supabase.table("scenes")
                    .select("id, status")
                    .eq("dataset_id", dataset_id)
                    .execute()
                )
                
                total_scenes = len(scenes_result.data)
                processed_scenes = sum(1 for s in scenes_result.data if s["status"] == "processed")
                
                # Get object count
                objects_result = (
                    self.supabase.table("objects")
                    .select("scene_id")
                    .in_("scene_id", [s["id"] for s in scenes_result.data])
                    .execute()
                )
                
                total_objects = len(objects_result.data)
                avg_objects = total_objects / total_scenes if total_scenes > 0 else 0
                completion_rate = (processed_scenes / total_scenes * 100) if total_scenes > 0 else 0
                
                stats.append({
                    "dataset_id": dataset_id,
                    "dataset_name": dataset["name"],
                    "total_scenes": total_scenes,
                    "processed_scenes": processed_scenes,
                    "total_objects": total_objects,
                    "avg_objects_per_scene": avg_objects,
                    "completion_rate": completion_rate
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get dataset stats: {e}")
            raise
    
    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary statistics"""
        try:
            # Get basic counts
            datasets_result = self.supabase.table("datasets").select("id").execute()
            scenes_result = self.supabase.table("scenes").select("id").execute()
            objects_result = self.supabase.table("objects").select("id").execute()
            
            total_datasets = len(datasets_result.data)
            total_scenes = len(scenes_result.data)
            total_objects = len(objects_result.data)
            
            # Scenes processed today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_scenes_result = (
                self.supabase.table("scenes")
                .select("id")
                .eq("status", "processed")
                .gte("created_at", today_start.isoformat())
                .execute()
            )
            scenes_today = len(today_scenes_result.data)
            
            # Active jobs
            active_jobs_result = (
                self.supabase.table("jobs")
                .select("id")
                .in_("status", ["queued", "running"])
                .execute()
            )
            active_jobs = len(active_jobs_result.data)
            
            # Average confidence
            scene_confs_result = (
                self.supabase.table("scenes")
                .select("scene_conf")
                .is_not("scene_conf", "null")
                .execute()
            )
            
            object_confs_result = (
                self.supabase.table("objects")
                .select("confidence")
                .execute()
            )
            
            scene_confs = [s["scene_conf"] for s in scene_confs_result.data]
            object_confs = [o["confidence"] for o in object_confs_result.data]
            
            all_confs = scene_confs + object_confs
            avg_confidence = sum(all_confs) / len(all_confs) if all_confs else 0
            
            # Recent activity (simplified)
            recent_activity = [
                {
                    "type": "dataset_created", 
                    "message": "New dataset uploaded", 
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "type": "job_completed", 
                    "message": "Processing job completed", 
                    "timestamp": (datetime.utcnow() - timedelta(minutes=15)).isoformat()
                }
            ]
            
            return {
                "total_datasets": total_datasets,
                "total_scenes": total_scenes,
                "total_objects": total_objects,
                "scenes_processed_today": scenes_today,
                "active_jobs": active_jobs,
                "avg_confidence": avg_confidence,
                "system_health_score": 95.0,  # Mock health score
                "recent_activity": recent_activity
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard summary: {e}")
            raise
    
    # Mock implementations for trends (would use proper time-series data)
    async def get_processing_trends(self, hours: int = 24, interval: int = 1) -> List[Dict[str, Any]]:
        """Get processing trend data (mock implementation)"""
        trends = []
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        for i in range(0, hours, interval):
            timestamp = start_time + timedelta(hours=i)
            trends.append({
                "timestamp": timestamp.isoformat(),
                "scenes_processed": max(0, 10 + i - 5),  # Mock trending data
                "avg_processing_time": 15.0 + (i % 3) * 2,  # Mock varying processing time
                "success_rate": 95.0 + (i % 5) * 1  # Mock success rate
            })
        
        return trends
    
    async def get_system_trends(self, hours: int = 24, interval: int = 1) -> List[Dict[str, Any]]:
        """Get system metrics trends (mock implementation)"""
        trends = []
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        for i in range(0, hours, interval):
            timestamp = start_time + timedelta(hours=i)
            trends.append({
                "timestamp": timestamp.isoformat(),
                "cpu_usage": 20.0 + (i % 5) * 10,  # Mock CPU usage
                "memory_usage": 1024 + (i % 3) * 256,  # Mock memory usage
                "queue_length": max(0, 5 - i % 8),  # Mock queue length
                "active_jobs": max(0, 3 - i % 5)  # Mock active jobs
            })
        
        return trends