#!/usr/bin/env python3
"""
Test batch processing with UUID fix
"""

import asyncio
import logging
import uuid
import sys
import os
from PIL import Image
import io

# Add the backend path to Python path
sys.path.append('/Users/leslieisah/MDM/backend')

from app.worker.batch_helpers import process_scenes_batch
from app.services.scenes import SceneService
from app.services.storage import StorageService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_batch_with_uuid_fix():
    """Test batch processing with UUID scene IDs"""
    
    print("🧪 Testing batch processing with UUID fix...")
    
    # Create test scenes with UUID IDs (simulating database data)
    test_scenes = []
    
    for i in range(3):
        # Create a simple test image
        img = Image.new('RGB', (640, 480), color=['red', 'green', 'blue'][i])
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 300, 200], fill='brown')  # Chair-like shape
        draw.rectangle([400, 200, 500, 400], fill='tan')    # Table-like shape
        
        # Convert to bytes
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=90)
        image_data = buf.getvalue()
        
        # Create scene with UUID (this was causing the JSON serialization error)
        scene_uuid = uuid.uuid4()  # This is a UUID object, not a string
        
        test_scenes.append({
            "scene_id": scene_uuid,  # UUID object - this should now be handled properly
            "image_data": image_data,
            "scene_data": {
                "title": f"Test Scene {i+1}",
                "description": f"Test scene with UUID {scene_uuid}"
            }
        })
        
        print(f"   Created scene {i+1} with UUID: {scene_uuid} (type: {type(scene_uuid)})")
    
    # Initialize services (proper initialization needed)
    from app.core.supabase import init_supabase
    from app.core.redis import init_redis
    
    # Initialize dependencies
    await init_supabase()
    await init_redis()
    
    scene_service = SceneService()
    storage_service = StorageService()
    
    print(f"\n🚀 Processing batch of {len(test_scenes)} scenes...")
    
    try:
        # Process the batch
        results = await process_scenes_batch(
            test_scenes, 
            scene_service, 
            storage_service,
            batch_size=3
        )
        
        print(f"✅ Batch processing completed!")
        print(f"📊 Results: {len(results)} scenes processed")
        
        # Analyze results
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        print(f"   ✅ Successful: {len(successful)}")
        print(f"   ❌ Failed: {len(failed)}")
        
        if successful:
            print("\n✅ Successful scenes:")
            for result in successful:
                scene_id = result.get('scene_id', 'unknown')
                processing_time = result.get('processing_time', 0)
                print(f"   - Scene {scene_id}: {processing_time}s")
        
        if failed:
            print("\n❌ Failed scenes:")
            for result in failed:
                scene_id = result.get('scene_id', 'unknown')
                error = result.get('error', 'Unknown error')
                print(f"   - Scene {scene_id}: {error}")
        
        # Check if the UUID serialization error is fixed
        uuid_error_found = any('UUID' in str(r.get('error', '')) for r in failed)
        
        if not uuid_error_found and len(results) > 0:
            print("\n🎉 UUID JSON serialization fix successful!")
            return True
        else:
            print("\n⚠️ UUID serialization issue may still exist")
            return False
            
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_individual_processing():
    """Test individual scene processing to compare"""
    
    print("\n🔄 Testing individual scene processing for comparison...")
    
    from app.services.ai_pipeline import process_scene_ai
    
    # Create a simple test image
    img = Image.new('RGB', (640, 480), color='purple')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([150, 150, 350, 300], fill='orange')  # Furniture shape
    
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    image_data = buf.getvalue()
    
    try:
        # Test with string scene_id
        result = await process_scene_ai(image_data, "individual_test_001")
        
        status = result.get('status', 'unknown')
        scene_type = result.get('scene_type', 'unknown')
        objects_detected = result.get('objects_detected', 0)
        
        print(f"   ✅ Individual processing: {status}")
        print(f"   🏠 Scene: {scene_type}")
        print(f"   🪑 Objects: {objects_detected}")
        
        return status == 'completed'
        
    except Exception as e:
        print(f"   ❌ Individual processing failed: {e}")
        return False

async def main():
    """Run comprehensive batch processing tests"""
    
    print("🔧 Testing Batch Processing with UUID Fix")
    print("=" * 50)
    
    # Test 1: Individual processing (baseline)
    individual_success = await test_individual_processing()
    
    # Test 2: Batch processing with UUIDs
    batch_success = await test_batch_with_uuid_fix()
    
    # Results
    print("\n" + "=" * 50)
    print("🎯 TEST RESULTS:")
    print(f"   Individual Processing: {'✅ PASS' if individual_success else '❌ FAIL'}")
    print(f"   Batch Processing (UUID Fix): {'✅ PASS' if batch_success else '❌ FAIL'}")
    
    overall_success = individual_success and batch_success
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("📝 Batch processing with UUIDs is working correctly!")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("🔧 Further debugging may be needed")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)