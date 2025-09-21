#!/usr/bin/env python3
"""
Check the specific Celery task result
"""

import os
import sys
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_task_result():
    """Check the specific task result in Redis"""
    task_id = "567d917e-57ca-4d75-9d1c-29cd879ad6a2"
    
    print(f"🔍 Checking Celery task result: {task_id}")
    print("=" * 70)
    
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
        
        # Get the task result
        task_key = f"celery-task-meta-{task_id}"
        task_result = redis_client.get(task_key)
        
        if task_result:
            task_data = json.loads(task_result.decode())
            
            print("✅ Task result found:")
            print(f"   Status: {task_data.get('status')}")
            print(f"   Task ID: {task_data.get('task_id')}")
            print(f"   Date Done: {task_data.get('date_done')}")
            
            result = task_data.get('result')
            if result:
                print(f"   Result:")
                if isinstance(result, dict):
                    for key, value in result.items():
                        print(f"     - {key}: {value}")
                else:
                    print(f"     {result}")
            
            # Check for error information
            if 'traceback' in task_data:
                print(f"   Traceback: {task_data.get('traceback')}")
            
            if 'exception' in task_data:
                print(f"   Exception: {task_data.get('exception')}")
                
        else:
            print("❌ Task result not found in Redis")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking task result: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_recent_jobs_in_db():
    """Check recent jobs in the database to understand what happened"""
    print(f"\n🔍 Checking recent jobs in database")
    print("=" * 50)
    
    try:
        import asyncio
        
        async def async_check():
            from app.core.supabase import init_supabase, get_supabase
            
            await init_supabase()
            supabase = get_supabase()
            
            # Get recent jobs
            result = supabase.table("jobs").select("*").order("created_at", desc=True).limit(10).execute()
            
            if result.data:
                print(f"   Found {len(result.data)} recent jobs:")
                for job in result.data:
                    print(f"     - {job.get('id')[:8]}... {job.get('kind')} {job.get('status')} "
                          f"Dataset: {job.get('dataset_id')} "
                          f"Created: {job.get('created_at')}")
                    
                    # Show meta if available
                    meta = job.get('meta', {})
                    if meta and 'celery_task_id' in meta:
                        celery_id = meta['celery_task_id']
                        print(f"       Celery ID: {celery_id}")
            else:
                print("   No jobs found in database")
        
        asyncio.run(async_check())
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def main():
    """Run checks"""
    check_task_result()
    check_recent_jobs_in_db()

if __name__ == "__main__":
    main()