"""
Celery application setup for background job processing
"""

import os
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "modomo_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.worker.tasks', 'app.worker.huggingface_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_expires=3600,  # 1 hour
    task_track_started=True,
    task_time_limit=settings.JOB_TIMEOUT,
    task_soft_time_limit=settings.JOB_TIMEOUT - 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True
)

# Task routing - route tasks to specific queues for better control
celery_app.conf.task_routes = {
    'process_dataset': {'queue': 'scene_processing'},
    'process_scene': {'queue': 'scene_processing'},
    'process_scenes_in_dataset': {'queue': 'scene_processing'},
    'cleanup_job': {'queue': 'scene_processing'},
    'app.worker.huggingface_tasks.process_huggingface_dataset': {'queue': 'scene_processing'},
    'app.worker.huggingface_tasks.validate_huggingface_url': {'queue': 'scene_processing'},
}

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.worker'])

# Import tasks explicitly to ensure registration  
try:
    from app.worker import tasks, huggingface_tasks
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import Celery tasks: {e}")
    pass

if __name__ == '__main__':
    celery_app.start()