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

# Task routing
celery_app.conf.task_routes = {
    'app.worker.tasks.process_dataset': {'queue': 'dataset_processing'},
    'app.worker.tasks.process_scene': {'queue': 'scene_processing'},
    'app.worker.tasks.cleanup_job': {'queue': 'maintenance'},
    'app.worker.huggingface_tasks.process_huggingface_dataset': {'queue': 'huggingface'},
    'app.worker.huggingface_tasks.validate_huggingface_url': {'queue': 'huggingface'},
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