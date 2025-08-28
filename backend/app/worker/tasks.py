"""
Celery tasks for background job processing
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from celery import current_task
from app.worker.celery_app import celery_app
from app.services.jobs import JobService
from app.services.datasets import DatasetService
from app.services.scenes import SceneService
from app.core.supabase import init_supabase, get_supabase
from app.core.redis import init_redis

logger = logging.getLogger(__name__)

def run_async(coro):
    """Helper to run async functions in Celery tasks"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

@celery_app.task(bind=True, name='process_dataset', max_retries=3, default_retry_delay=60)
def process_dataset(self, job_id: str, dataset_id: str, options: Dict[str, Any] = None):
    """
    Process an entire dataset - main background job for dataset ingestion
    """
    logger.info(f"Starting dataset processing job {job_id} for dataset {dataset_id}")
    
    async def _process():
        # Initialize connections for worker process
        await init_supabase()
        await init_redis()
        
        job_service = JobService()
        dataset_service = DatasetService()
        
        try:
            # Update job status to running
            await job_service.update_job(job_id, {
                "status": "running",
                "started_at": datetime.utcnow().isoformat()
            })
            
            # Add job event
            await job_service.add_job_event(job_id, "started", {
                "stage": "dataset_processing",
                "dataset_id": dataset_id
            })
            
            # Get dataset info
            dataset = await dataset_service.get_dataset(dataset_id)
            if not dataset:
                raise Exception(f"Dataset {dataset_id} not found")
            
            # Simulate dataset processing steps
            stages = [
                ("validating", "Validating dataset structure"),
                ("scanning", "Scanning for images"),
                ("preprocessing", "Preprocessing images"),
                ("extracting", "Extracting metadata"),
                ("registering", "Registering scenes")
            ]
            
            total_stages = len(stages)
            for i, (stage, description) in enumerate(stages):
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': total_stages,
                        'stage': stage,
                        'description': description
                    }
                )
                
                # Add stage event
                await job_service.add_job_event(job_id, "progress", {
                    "stage": stage,
                    "description": description,
                    "progress": (i + 1) / total_stages * 100
                })
                
                # Simulate processing time
                await asyncio.sleep(2)
            
            # Complete the job
            await job_service.update_job(job_id, {
                "status": "succeeded",
                "finished_at": datetime.utcnow().isoformat(),
                "result": {
                    "processed_scenes": 10,  # Mock result
                    "success_rate": 100,
                    "processing_time": 10
                }
            })
            
            await job_service.add_job_event(job_id, "completed", {
                "stage": "finished",
                "processed_scenes": 10
            })
            
            logger.info(f"Dataset processing job {job_id} completed successfully")
            return {"status": "success", "processed_scenes": 10}
            
        except Exception as e:
            logger.error(f"Dataset processing job {job_id} failed: {e}")
            
            # Check if we should retry
            if self.request.retries < self.max_retries:
                logger.info(f"Retrying dataset processing (attempt {self.request.retries + 1}/{self.max_retries})")
                
                # Add retry event
                await job_service.add_job_event(job_id, "retry", {
                    "attempt": self.request.retries + 1,
                    "max_retries": self.max_retries,
                    "error": str(e),
                    "stage": "retry"
                })
                
                # Mark job as retrying
                await job_service.update_job(job_id, {
                    "status": "retrying",
                    "error": f"Attempt {self.request.retries + 1}/{self.max_retries}: {str(e)}"
                })
                
                raise self.retry(exc=e)
            
            # Mark job as failed after all retries exhausted
            await job_service.update_job(job_id, {
                "status": "failed",
                "finished_at": datetime.utcnow().isoformat(),
                "error": str(e)
            })
            
            await job_service.add_job_event(job_id, "failed", {
                "error": str(e),
                "stage": "error",
                "retries_exhausted": True
            })
            
            raise e
    
    return run_async(_process())

@celery_app.task(bind=True, name='process_scene', max_retries=2, default_retry_delay=30)
def process_scene(self, job_id: str, scene_id: str, options: Dict[str, Any] = None):
    """
    Process a single scene - AI analysis pipeline
    """
    logger.info(f"Starting scene processing job {job_id} for scene {scene_id}")
    
    async def _process():
        # Initialize connections for worker process
        await init_supabase()
        await init_redis()
        
        job_service = JobService()
        scene_service = SceneService()
        
        try:
            # Update job status
            await job_service.update_job(job_id, {
                "status": "running",
                "started_at": datetime.utcnow().isoformat()
            })
            
            await job_service.add_job_event(job_id, "started", {
                "stage": "scene_processing",
                "scene_id": scene_id
            })
            
            # Get scene info
            scene = await scene_service.get_scene(scene_id, include_objects=False)
            if not scene:
                raise Exception(f"Scene {scene_id} not found")
            
            # Simulate AI processing pipeline
            ai_stages = [
                ("loading", "Loading image"),
                ("scene_classification", "Classifying scene type"),
                ("object_detection", "Detecting objects"),
                ("segmentation", "Generating masks"),
                ("depth_estimation", "Estimating depth"),
                ("style_analysis", "Analyzing design style"),
                ("material_classification", "Classifying materials"),
                ("quality_assessment", "Assessing image quality")
            ]
            
            total_stages = len(ai_stages)
            for i, (stage, description) in enumerate(ai_stages):
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': total_stages,
                        'stage': stage,
                        'description': description,
                        'scene_id': scene_id
                    }
                )
                
                await job_service.add_job_event(job_id, "progress", {
                    "stage": stage,
                    "description": description,
                    "scene_id": scene_id,
                    "progress": (i + 1) / total_stages * 100
                })
                
                # Simulate AI processing time
                await asyncio.sleep(1.5)
            
            # Update scene with mock AI results
            ai_results = {
                "status": "processed",
                "scene_type": "living_room",
                "scene_conf": 0.92,
                "style": "contemporary",
                "objects_detected": 8,
                "processing_time": len(ai_stages) * 1.5
            }
            
            await scene_service.update_scene(scene_id, ai_results)
            
            # Complete job
            await job_service.update_job(job_id, {
                "status": "succeeded", 
                "finished_at": datetime.utcnow().isoformat(),
                "result": ai_results
            })
            
            await job_service.add_job_event(job_id, "completed", {
                "stage": "finished",
                "scene_id": scene_id,
                **ai_results
            })
            
            logger.info(f"Scene processing job {job_id} completed successfully")
            return ai_results
            
        except Exception as e:
            logger.error(f"Scene processing job {job_id} failed: {e}")
            
            # Check if we should retry
            if self.request.retries < self.max_retries:
                logger.info(f"Retrying scene processing (attempt {self.request.retries + 1}/{self.max_retries})")
                
                # Add retry event
                await job_service.add_job_event(job_id, "retry", {
                    "attempt": self.request.retries + 1,
                    "max_retries": self.max_retries,
                    "error": str(e),
                    "scene_id": scene_id,
                    "stage": "retry"
                })
                
                # Mark job as retrying
                await job_service.update_job(job_id, {
                    "status": "retrying",
                    "error": f"Attempt {self.request.retries + 1}/{self.max_retries}: {str(e)}"
                })
                
                raise self.retry(exc=e)
            
            # Mark job as failed after all retries exhausted
            await job_service.update_job(job_id, {
                "status": "failed",
                "finished_at": datetime.utcnow().isoformat(),
                "error": str(e)
            })
            
            await job_service.add_job_event(job_id, "failed", {
                "error": str(e),
                "scene_id": scene_id,
                "stage": "error",
                "retries_exhausted": True
            })
            
            raise e
    
    return run_async(_process())

@celery_app.task(bind=True, name='cleanup_job')
def cleanup_job(self, job_id: str):
    """
    Cleanup job - remove temporary files and old job data
    """
    logger.info(f"Starting cleanup job {job_id}")
    
    async def _cleanup():
        job_service = JobService()
        
        try:
            # Mock cleanup operations
            await asyncio.sleep(1)
            
            await job_service.add_job_event(job_id, "cleanup_completed", {
                "stage": "maintenance",
                "cleaned_files": 0  # Mock
            })
            
            logger.info(f"Cleanup job {job_id} completed")
            return {"status": "success", "cleaned_files": 0}
            
        except Exception as e:
            logger.error(f"Cleanup job {job_id} failed: {e}")
            raise e
    
    return run_async(_cleanup())

# Task result callbacks
@celery_app.task(bind=True)
def task_success_handler(self, retval, task_id, args, kwargs):
    """Handle successful task completion"""
    logger.info(f"Task {task_id} completed successfully: {retval}")

@celery_app.task(bind=True)
def task_failure_handler(self, task_id, error, traceback, args, kwargs):
    """Handle task failure"""
    logger.error(f"Task {task_id} failed with error: {error}")
    logger.error(f"Traceback: {traceback}")