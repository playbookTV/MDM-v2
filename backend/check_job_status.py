#!/usr/bin/env python3
"""
Check the status of the specific job ID from the UI
"""

import os
import sys
import asyncio
import logging

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def check_job_status():
    """Check the specific job status"""
    job_id = "567d917e-57ca-4d75-9d1c-29cd879ad6a2"
    
    print(f"🔍 Checking job status for: {job_id}")
    print("=" * 70)
    
    try:
        from app.core.supabase import init_supabase, get_supabase
        
        # Initialize Supabase
        await init_supabase()
        supabase = get_supabase()
        
        # Look up the job
        result = supabase.table("jobs").select("*").eq("id", job_id).execute()
        
        if result.data:
            job = result.data[0]
            print("✅ Job found in database:")
            print(f"   ID: {job.get('id')}")
            print(f"   Kind: {job.get('kind')}")
            print(f"   Status: {job.get('status')}")
            print(f"   Dataset ID: {job.get('dataset_id')}")
            print(f"   Created: {job.get('created_at')}")
            print(f"   Started: {job.get('started_at')}")
            print(f"   Finished: {job.get('finished_at')}")
            print(f"   Error: {job.get('error')}")
            
            meta = job.get('meta', {})
            if meta:
                print(f"   Meta:")
                for key, value in meta.items():
                    print(f"     - {key}: {value}")
            
            # Check if there's a Celery task ID
            celery_task_id = meta.get('celery_task_id')
            if celery_task_id:
                print(f"\n🔧 Celery Task ID: {celery_task_id}")
                
                # Check Redis for task status
                try:
                    import redis
                    from app.core.config import settings
                    
                    # Connect to Redis to check task status
                    if hasattr(settings, 'REDIS_URL'):
                        redis_client = redis.from_url(settings.REDIS_URL)
                    else:
                        redis_client = redis.Redis(
                            host=getattr(settings, 'REDIS_HOST', 'localhost'),
                            port=getattr(settings, 'REDIS_PORT', 6379),
                            password=getattr(settings, 'REDIS_PASSWORD', None)
                        )
                    
                    # Check if task is in Redis
                    task_key = f"celery-task-meta-{celery_task_id}"
                    task_result = redis_client.get(task_key)
                    
                    if task_result:
                        import json
                        task_data = json.loads(task_result.decode())
                        print(f"   Redis Task Status: {task_data.get('status')}")
                        print(f"   Task Result: {task_data.get('result')}")
                        if 'traceback' in task_data:
                            print(f"   Error Traceback: {task_data.get('traceback')[:500]}...")
                    else:
                        print(f"   ⚠️  Task not found in Redis (may have expired)")
                        
                        # Check for active/pending tasks
                        pending_tasks = redis_client.llen('celery')
                        print(f"   Pending tasks in queue: {pending_tasks}")
                        
                except Exception as e:
                    print(f"   ❌ Redis task check failed: {e}")
            else:
                print(f"\n⚠️  No Celery task ID found - job may not have been processed")
                
        else:
            print("❌ Job not found in database")
            return False
            
        # Also check for any related jobs
        print(f"\n🔍 Checking for related jobs...")
        if result.data:
            dataset_id = result.data[0].get('dataset_id')
            if dataset_id:
                related_result = supabase.table("jobs").select("*").eq("dataset_id", dataset_id).order("created_at", desc=True).limit(5).execute()
                
                if related_result.data:
                    print(f"   Found {len(related_result.data)} jobs for dataset {dataset_id}:")
                    for job in related_result.data:
                        print(f"     - {job.get('id')[:8]}... {job.get('kind')} {job.get('status')} ({job.get('created_at')})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking job: {e}")
        import traceback
        traceback.print_exc()
        return False

async def check_celery_queue():
    """Check what's in the Celery queue"""
    print(f"\n🔧 Checking Celery Queue Status")
    print("=" * 50)
    
    try:
        import redis
        from app.core.config import settings
        
        if hasattr(settings, 'REDIS_URL'):
            redis_client = redis.from_url(settings.REDIS_URL)
        else:
            redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                password=getattr(settings, 'REDIS_PASSWORD', None)
            )
        
        # Check queue lengths
        queues = ['celery', 'huggingface', 'dataset_processing', 'scene_processing', 'maintenance']
        for queue in queues:
            length = redis_client.llen(queue)
            print(f"   Queue '{queue}': {length} pending tasks")
        
        # Check for any recent task results
        keys = redis_client.keys('celery-task-meta-*')
        print(f"   Total task results in Redis: {len(keys)}")
        
        if keys:
            print(f"   Recent task results:")
            for key in keys[-5:]:  # Show last 5
                task_id = key.decode().replace('celery-task-meta-', '')
                result = redis_client.get(key)
                if result:
                    import json
                    data = json.loads(result.decode())
                    status = data.get('status', 'unknown')
                    print(f"     - {task_id[:8]}... {status}")
        
    except Exception as e:
        print(f"❌ Error checking queue: {e}")

async def main():
    """Run all checks"""
    await check_job_status()
    await check_celery_queue()

if __name__ == "__main__":
    asyncio.run(main())