#!/usr/bin/env python3
"""
Check the failed AI processing job
"""

import os
import sys
import asyncio

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def check_failed_job():
    """Check the failed AI processing job"""
    failed_job_id = "ad94c9aa-c7f8-4e6b-9c90-c0fc8b1b9aef"  # From the output above
    
    print(f"🔍 Checking failed AI processing job: {failed_job_id}")
    print("=" * 70)
    
    try:
        from app.core.supabase import init_supabase, get_supabase
        
        await init_supabase()
        supabase = get_supabase()
        
        # Get the failed job details
        result = supabase.table("jobs").select("*").eq("id", failed_job_id).execute()
        
        if result.data:
            job = result.data[0]
            print("❌ Failed job details:")
            print(f"   ID: {job.get('id')}")
            print(f"   Kind: {job.get('kind')}")
            print(f"   Status: {job.get('status')}")
            print(f"   Dataset ID: {job.get('dataset_id')}")
            print(f"   Created: {job.get('created_at')}")
            print(f"   Started: {job.get('started_at')}")
            print(f"   Finished: {job.get('finished_at')}")
            
            error = job.get('error')
            if error:
                print(f"   Error: {error}")
            
            meta = job.get('meta', {})
            if meta:
                print(f"   Meta:")
                for key, value in meta.items():
                    print(f"     - {key}: {value}")
                    
            # Check if the dataset has scenes
            dataset_id = job.get('dataset_id')
            if dataset_id:
                print(f"\n🔍 Checking scenes in dataset {dataset_id}:")
                scenes_result = supabase.table("scenes").select("id, source, created_at").eq("dataset_id", dataset_id).limit(5).execute()
                
                if scenes_result.data:
                    print(f"   ✅ Found {len(scenes_result.data)} scenes (showing first 5):")
                    for scene in scenes_result.data:
                        print(f"     - {scene.get('id')[:8]}... Source: {scene.get('source')} Created: {scene.get('created_at')}")
                else:
                    print(f"   ❌ No scenes found in dataset")
        else:
            print("❌ Failed job not found")
            
    except Exception as e:
        print(f"❌ Error checking failed job: {e}")
        import traceback
        traceback.print_exc()

async def check_dataset_status():
    """Check the overall dataset status"""
    dataset_id = "c462997f-e51a-405b-accf-1b57e3138773"
    
    print(f"\n📊 Checking dataset status: {dataset_id}")
    print("=" * 50)
    
    try:
        from app.core.supabase import init_supabase, get_supabase
        
        await init_supabase()
        supabase = get_supabase()
        
        # Get dataset info
        dataset_result = supabase.table("datasets").select("*").eq("id", dataset_id).execute()
        
        if dataset_result.data:
            dataset = dataset_result.data[0]
            print(f"✅ Dataset found:")
            print(f"   Name: {dataset.get('name')}")
            print(f"   Description: {dataset.get('description')}")
            print(f"   Created: {dataset.get('created_at')}")
            
            # Count scenes
            scenes_count = supabase.table("scenes").select("id", count="exact").eq("dataset_id", dataset_id).execute()
            print(f"   Total scenes: {scenes_count.count}")
            
            # Count objects  
            objects_result = supabase.table("objects").select("scene_id", count="exact").execute()
            # Filter by scenes in this dataset
            scene_ids_result = supabase.table("scenes").select("id").eq("dataset_id", dataset_id).execute()
            scene_ids = [s['id'] for s in scene_ids_result.data] if scene_ids_result.data else []
            
            if scene_ids:
                objects_count = supabase.table("objects").select("id", count="exact").in_("scene_id", scene_ids).execute()
                print(f"   Total objects: {objects_count.count}")
            
            # Check recent jobs for this dataset
            jobs_result = supabase.table("jobs").select("*").eq("dataset_id", dataset_id).order("created_at", desc=True).execute()
            
            if jobs_result.data:
                print(f"   Recent jobs:")
                for job in jobs_result.data:
                    print(f"     - {job.get('kind')} {job.get('status')} ({job.get('created_at')})")
        else:
            print("❌ Dataset not found")
            
    except Exception as e:
        print(f"❌ Error checking dataset: {e}")

async def main():
    await check_failed_job()
    await check_dataset_status()

if __name__ == "__main__":
    asyncio.run(main())