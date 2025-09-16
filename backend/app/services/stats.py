"""
Statistics service using Supabase client
"""

import logging
import psutil
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.supabase import get_supabase
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

# Track app start time for uptime calculation
APP_START_TIME = time.time()

class StatsService:
    """Service for statistics operations"""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.redis = get_redis()
    
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
            
            # Test Redis connectivity
            redis_status = "healthy"
            if self.redis:
                try:
                    await self.redis.ping()
                    redis_status = "healthy"
                except Exception as e:
                    logger.warning(f"Redis health check failed: {e}")
                    redis_status = "error"
            else:
                redis_status = "unavailable"
            
            return {
                "status": "healthy" if db_status == "healthy" and redis_status in ["healthy", "unavailable"] else "unhealthy",
                "database_status": db_status,
                "storage_status": "healthy",  # TODO: Test R2 connectivity
                "queue_status": redis_status,
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
            
            # Get real processing times from jobs
            processing_times = []
            avg_processing_time = 15.0  # Default fallback
            if jobs_result.data:
                for job in jobs_result.data:
                    if job["status"] == "succeeded" and job.get("meta") and isinstance(job["meta"], dict):
                        proc_time = job["meta"].get("processing_time")
                        if proc_time and isinstance(proc_time, (int, float)):
                            processing_times.append(proc_time)
                
                if processing_times:
                    avg_processing_time = sum(processing_times) / len(processing_times)
            
            # Get current queue length from Redis
            queue_length = 0
            if self.redis:
                try:
                    from app.core.config import settings
                    queue_length = await self.redis.llen(settings.REDIS_JOB_QUEUE)
                except Exception as e:
                    logger.warning(f"Failed to get queue length: {e}")
            
            return {
                "total_scenes_processed": processed_scenes,
                "avg_processing_time_seconds": round(avg_processing_time, 1),
                "scenes_per_hour": round(scenes_per_hour, 1),
                "success_rate_percent": round(success_rate, 1),
                "error_rate_percent": round(error_rate, 1),
                "queue_length": queue_length
            }
            
        except Exception as e:
            logger.error(f"Failed to get processing metrics: {e}")
            raise
    
    async def get_model_performance(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get AI model performance metrics"""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            # Scene classification performance
            try:
                scenes_result = (
                    self.supabase.table("scenes")
                    .select("scene_conf")
                    .not_.is_("scene_conf", "null")
                    .gte("created_at", since.isoformat())
                    .execute()
                )
                
                scene_confs = [s["scene_conf"] for s in scenes_result.data if s["scene_conf"] is not None]
                scene_count = len(scene_confs)
                scene_avg_conf = sum(scene_confs) / scene_count if scene_count > 0 else 0.85
                scene_high_conf = sum(1 for c in scene_confs if c >= 0.8) if scene_count > 0 else 0
                scene_low_conf = sum(1 for c in scene_confs if c < 0.5) if scene_count > 0 else 0
            except Exception as e:
                logger.warning(f"Error getting scene confidence data: {e}")
                scene_confs, scene_count, scene_avg_conf, scene_high_conf, scene_low_conf = [], 0, 0.85, 0, 0
            
            # Object detection performance
            try:
                objects_result = (
                    self.supabase.table("objects")
                    .select("confidence")
                    .gte("created_at", since.isoformat())
                    .execute()
                )
                
                object_confs = [o["confidence"] for o in objects_result.data if o["confidence"] is not None]
                object_count = len(object_confs)
                object_avg_conf = sum(object_confs) / object_count if object_count > 0 else 0.82
                object_high_conf = sum(1 for c in object_confs if c >= 0.8) if object_count > 0 else 0
                object_low_conf = sum(1 for c in object_confs if c < 0.5) if object_count > 0 else 0
            except Exception as e:
                logger.warning(f"Error getting object confidence data: {e}")
                object_confs, object_count, object_avg_conf, object_high_conf, object_low_conf = [], 0, 0.82, 0, 0
            
            return [
                {
                    "model_name": "Scene Classifier",
                    "avg_confidence": scene_avg_conf,
                    "predictions_count": scene_count,
                    "high_confidence_rate": (scene_high_conf / scene_count * 100) if scene_count > 0 else 85.0,
                    "low_confidence_rate": (scene_low_conf / scene_count * 100) if scene_count > 0 else 5.0
                },
                {
                    "model_name": "Object Detector",
                    "avg_confidence": object_avg_conf,
                    "predictions_count": object_count,
                    "high_confidence_rate": (object_high_conf / object_count * 100) if object_count > 0 else 82.0,
                    "low_confidence_rate": (object_low_conf / object_count * 100) if object_count > 0 else 8.0
                }
            ]
            
        except Exception as e:
            logger.error(f"Failed to get model performance: {e}")
            # Return mock data when database fails
            return [
                {
                    "model_name": "Scene Classifier",
                    "avg_confidence": 0.85,
                    "predictions_count": 0,
                    "high_confidence_rate": 85.0,
                    "low_confidence_rate": 5.0
                },
                {
                    "model_name": "Object Detector", 
                    "avg_confidence": 0.82,
                    "predictions_count": 0,
                    "high_confidence_rate": 82.0,
                    "low_confidence_rate": 8.0
                }
            ]
    
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
                .not_.is_("scene_conf", "null")
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
            
            # Calculate system health score based on real metrics  
            health_score = 100.0
            if avg_confidence < 0.7:
                health_score -= 10
            if active_jobs > 10:
                health_score -= 5
            if scenes_today == 0:
                health_score -= 5
                
            # Get recent activity from job events
            try:
                recent_jobs = (
                    self.supabase.table("jobs")
                    .select("*")
                    .order("created_at", desc=True)
                    .limit(5)
                    .execute()
                )
                
                recent_activity = []
                for job in recent_jobs.data:
                    activity_type = "job_completed" if job["status"] == "succeeded" else "job_failed"
                    message = f"Job {job['type']} {job['status']}"
                    recent_activity.append({
                        "type": activity_type,
                        "message": message,
                        "timestamp": job.get("finished_at") or job.get("created_at")
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to get recent activity: {e}")
                recent_activity = [
                    {
                        "type": "system_start",
                        "message": "System monitoring active",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ]
            
            return {
                "total_datasets": total_datasets,
                "total_scenes": total_scenes,
                "total_objects": total_objects,
                "scenes_processed_today": scenes_today,
                "active_jobs": active_jobs,
                "avg_confidence": round(avg_confidence, 3),
                "system_health_score": round(health_score, 1),
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