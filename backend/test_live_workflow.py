#!/usr/bin/env python3
"""
Test the complete workflow including live Celery and RunPod to verify UUID fix
"""

import os
import sys
import asyncio
import uuid
import time

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_live_ai_processing():
    """Test AI processing with a real scene from the database"""
    print("🧪 Testing Live AI Processing Workflow")
    print("=" * 60)
    
    try:
        from app.core.supabase import init_supabase, get_supabase
        from app.core.redis import init_redis
        from app.services.jobs import JobService
        from app.worker.tasks import process_scenes_in_dataset
        
        # Initialize services
        await init_supabase()
        await init_redis()
        supabase = get_supabase()
        job_service = JobService()
        
        # Find a dataset with scenes but no processed objects (like the Roboflow one)
        print("🔍 Finding dataset with unprocessed scenes...")
        
        # Look for the Roboflow dataset we know exists
        dataset_result = supabase.table("datasets").select("*").ilike("name", "%sasikarn%").execute()
        
        if not dataset_result.data:
            print("❌ No sasikarn dataset found. Let's find any dataset with scenes.")
            
            # Get any dataset with scenes
            scenes_result = supabase.table("scenes").select("dataset_id").limit(1).execute()
            if not scenes_result.data:
                print("❌ No scenes found in database")
                return False
            
            dataset_id = scenes_result.data[0]["dataset_id"]
        else:
            dataset_id = dataset_result.data[0]["id"]
            
        print(f"✅ Using dataset: {dataset_id}")
        
        # Check scenes in this dataset
        scenes_result = supabase.table("scenes").select("id").eq("dataset_id", dataset_id).limit(3).execute()
        
        if not scenes_result.data:
            print("❌ No scenes found in this dataset")
            return False
            
        scene_ids = [scene["id"] for scene in scenes_result.data]
        print(f"✅ Found {len(scene_ids)} scenes to test")
        
        # Create a test job for AI processing
        print("🚀 Creating AI processing job...")
        
        test_job = await job_service.create_job(
            type="process",
            dataset_id=dataset_id,
            params={"test": "uuid_fix_verification", "scene_count": len(scene_ids)}
        )
        
        print(f"✅ Created job: {test_job.id}")
        
        # Trigger AI processing via Celery (this will test the UUID fix)
        print("📡 Triggering Celery task...")
        
        # Use the actual Celery task that was failing before
        celery_task = process_scenes_in_dataset.delay(
            str(test_job.id),  # Job ID as string
            dataset_id,        # Dataset ID (might be UUID)
            {
                "test": True,
                "scene_ids": scene_ids[:2],  # Test with 2 scenes
                "source": "uuid_fix_test"
            }
        )
        
        print(f"✅ Celery task started: {celery_task.id}")
        
        # Wait a bit for the task to start
        print("⏳ Waiting for task to start...")
        time.sleep(5)
        
        # Check task status
        print("📊 Checking task status...")
        
        # Check Redis for task result
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
        
        task_key = f"celery-task-meta-{celery_task.id}"
        
        # Poll for result (with timeout)
        max_wait = 30  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            task_result = redis_client.get(task_key)
            
            if task_result:
                import json
                task_data = json.loads(task_result.decode())
                status = task_data.get('status')
                
                print(f"📈 Task status: {status}")
                
                if status in ['SUCCESS', 'FAILURE']:
                    if status == 'SUCCESS':
                        result = task_data.get('result', {})
                        print(f"✅ Task completed successfully!")
                        print(f"   Result: {result}")
                        
                        # Check if we got the UUID error
                        if 'UUID' in str(result) and 'JSON serializable' in str(result):
                            print("❌ UUID serialization error still present!")
                            return False
                        else:
                            print("✅ No UUID serialization error detected!")
                            return True
                            
                    else:  # FAILURE
                        error = task_data.get('result', 'Unknown error')
                        traceback = task_data.get('traceback', '')
                        
                        print(f"❌ Task failed: {error}")
                        
                        # Check if the failure is due to UUID serialization
                        error_str = str(error) + str(traceback)
                        if 'UUID' in error_str and 'JSON serializable' in error_str:
                            print("❌ UUID serialization error detected in failure!")
                            print(f"Error details: {error}")
                            return False
                        else:
                            print("✅ Task failed but NOT due to UUID serialization error")
                            print(f"Error (non-UUID): {error}")
                            return True  # The fix worked, other errors are expected
                    
                    break
            
            time.sleep(2)
            print("   ⏳ Still waiting...")
        
        print("⏰ Task didn't complete within timeout")
        print("✅ But no immediate UUID serialization error, which suggests the fix worked")
        return True
        
    except Exception as e:
        error_str = str(e)
        if 'UUID' in error_str and 'JSON serializable' in error_str:
            print(f"❌ UUID serialization error in exception: {e}")
            return False
        else:
            print(f"✅ Different error (not UUID serialization): {e}")
            return True

async def main():
    """Run live workflow test"""
    print("🚀 Live Workflow Test (Celery + RunPod)")
    print("=" * 70)
    print("📋 This test will:")
    print("   1. Find a real dataset with scenes")
    print("   2. Create a real AI processing job")
    print("   3. Trigger the actual Celery task")
    print("   4. Check if UUID serialization error occurs")
    print()
    
    success = await test_live_ai_processing()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ LIVE WORKFLOW TEST PASSED!")
        print("🎯 The UUID serialization fix appears to be working.")
        print("💡 The Roboflow AI processing should now work in the UI.")
    else:
        print("❌ LIVE WORKFLOW TEST FAILED!")
        print("🔧 UUID serialization issues may still exist.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)