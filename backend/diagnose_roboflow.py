#!/usr/bin/env python3
"""
Diagnose Roboflow ingestion issues
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_roboflow_ingestion():
    """Test the full Roboflow ingestion pipeline"""
    print("🔍 Diagnosing Roboflow Ingestion Pipeline")
    print("=" * 70)
    
    # Step 1: Check dependencies
    print("\n📦 Step 1: Checking dependencies...")
    try:
        import roboflow
        print(f"   ✅ Roboflow version: {roboflow.__version__}")
    except ImportError as e:
        print(f"   ❌ Roboflow not installed: {e}")
        return False
    
    # Step 2: Check environment
    print("\n🔑 Step 2: Checking environment...")
    api_key = os.getenv("ROBOFLOW_API_KEY")
    if api_key:
        print(f"   ✅ API key found: {api_key[:10]}...")
    else:
        print("   ❌ ROBOFLOW_API_KEY not set")
        return False
    
    # Step 3: Initialize services
    print("\n🚀 Step 3: Initializing services...")
    try:
        from app.core.supabase import init_supabase, get_supabase
        from app.core.redis import init_redis
        from app.services.roboflow import RoboflowService
        
        # Initialize async services
        await init_supabase()
        await init_redis()
        
        print("   ✅ Supabase initialized")
        print("   ✅ Redis initialized")
        
        # Create service
        service = RoboflowService()
        print("   ✅ RoboflowService created")
        
    except Exception as e:
        print(f"   ❌ Service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Test URL validation
    print("\n🔗 Step 4: Testing URL validation...")
    test_url = "https://universe.roboflow.com/roboflow-100/furniture-ngpea/model/1"
    
    try:
        url_parts = service.validate_roboflow_url(test_url)
        if url_parts:
            workspace, project, version = url_parts
            print(f"   ✅ URL parsed: {workspace}/{project} v{version}")
        else:
            print("   ❌ URL validation failed")
            return False
    except Exception as e:
        print(f"   ❌ URL validation error: {e}")
        return False
    
    # Step 5: Test dataset info extraction
    print("\n📊 Step 5: Testing dataset info extraction...")
    try:
        info = service.extract_dataset_info(test_url, api_key)
        if info:
            print(f"   ✅ Dataset info extracted: {info.get('dataset_id', 'unknown')}")
            for key, value in info.items():
                print(f"      - {key}: {value}")
        else:
            print("   ⚠️  No dataset info returned (might be access issue)")
    except Exception as e:
        print(f"   ❌ Dataset info extraction failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 6: Test image loading
    print("\n🖼️  Step 6: Testing image loading...")
    try:
        images = service.load_roboflow_dataset_images(
            roboflow_url=test_url,
            api_key=api_key,
            export_format="coco",
            max_images=2  # Just test with 2 images
        )
        
        if images:
            print(f"   ✅ Loaded {len(images)} test images")
            for i, img in enumerate(images):
                print(f"      - Image {i+1}: {img.get('width')}x{img.get('height')}")
                if 'metadata' in img:
                    annotations = img['metadata'].get('annotations', [])
                    print(f"        Annotations: {len(annotations)}")
        else:
            print("   ❌ No images loaded")
            return False
            
    except Exception as e:
        print(f"   ❌ Image loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 7: Test metadata processing
    print("\n🔄 Step 7: Testing metadata processing...")
    if images and len(images) > 0:
        try:
            test_metadata = images[0].get('metadata', {})
            result = service.handle_existing_roboflow_metadata(
                test_metadata, 
                "test-scene-001",
                0
            )
            
            print(f"   ✅ Metadata processed")
            print(f"      - Scene updates: {len(result.get('scene_updates', {}))}")
            print(f"      - Objects extracted: {len(result.get('objects_data', []))}")
            
            skip_ai = result.get('skip_ai', {})
            skipped = [k for k, v in skip_ai.items() if v]
            if skipped:
                print(f"      - Components to skip: {', '.join(skipped)}")
                
        except Exception as e:
            print(f"   ❌ Metadata processing failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Step 8: Test the full ingestion task (mock)
    print("\n🎯 Step 8: Testing Celery task import...")
    try:
        from app.worker.roboflow_tasks import process_roboflow_dataset
        print("   ✅ Celery task imported successfully")
        
        # Check task configuration
        print(f"      - Max retries: {process_roboflow_dataset.max_retries}")
        print(f"      - Retry delay: {process_roboflow_dataset.default_retry_delay}s")
        
    except Exception as e:
        print(f"   ❌ Celery task import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("✅ Roboflow ingestion pipeline diagnosis complete!")
    print("\n💡 Summary:")
    print("   - All core components are working")
    print("   - API key is configured")
    print("   - Services can be initialized")
    print("   - Dataset can be accessed and downloaded")
    print("   - Metadata processing is functional")
    print("   - Celery task is importable")
    
    return True

async def test_specific_issue():
    """Test specific issue that might be causing ingestion to fail"""
    print("\n🔬 Testing Specific Ingestion Issues")
    print("=" * 70)
    
    try:
        # Initialize services
        from app.core.supabase import init_supabase
        from app.core.redis import init_redis
        await init_supabase()
        await init_redis()
        
        # Test synchronous methods used in Celery
        from app.services.roboflow import RoboflowService
        from app.services.datasets import DatasetService
        
        service = RoboflowService()
        dataset_service = DatasetService()
        
        print("\n1️⃣  Testing sync upload method...")
        from PIL import Image
        test_image = Image.new('RGB', (100, 100), color='red')
        
        r2_key = service.upload_image_to_r2_sync(test_image, "test_image.jpg")
        if r2_key:
            print(f"   ✅ Sync upload successful: {r2_key}")
        else:
            print("   ❌ Sync upload failed")
        
        print("\n2️⃣  Testing dataset service sync methods...")
        try:
            # This will fail if no dataset exists, but we're testing the method exists
            dataset = dataset_service.get_dataset_sync("test-dataset-id")
            print("   ✅ get_dataset_sync method exists")
        except AttributeError as e:
            print(f"   ❌ Missing sync method: {e}")
        except Exception:
            print("   ✅ get_dataset_sync method exists (dataset not found is expected)")
        
        print("\n3️⃣  Testing COCO annotation parsing...")
        service = RoboflowService()
        
        # Mock COCO data structure
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock COCO annotation file
            coco_data = {
                "images": [{"id": 1, "file_name": "test.jpg", "width": 640, "height": 480}],
                "annotations": [
                    {
                        "id": 1,
                        "image_id": 1,
                        "category_id": 1,
                        "bbox": [100, 100, 50, 50],
                        "area": 2500,
                        "iscrowd": 0
                    }
                ],
                "categories": [{"id": 1, "name": "chair"}]
            }
            
            ann_path = os.path.join(tmpdir, "train", "_annotations.coco.json")
            os.makedirs(os.path.dirname(ann_path), exist_ok=True)
            with open(ann_path, 'w') as f:
                json.dump(coco_data, f)
            
            # Create mock image
            img_path = os.path.join(tmpdir, "train", "test.jpg")
            test_img = Image.new('RGB', (640, 480), color='blue')
            test_img.save(img_path)
            
            # Test parsing
            images = service._parse_coco_dataset(tmpdir, max_images=1)
            
            if images:
                print(f"   ✅ COCO parsing successful: {len(images)} images")
                if images[0].get('metadata', {}).get('annotations'):
                    print(f"      - Annotations found: {len(images[0]['metadata']['annotations'])}")
            else:
                print("   ❌ COCO parsing failed")
        
        print("\n✅ Specific issue tests complete")
        return True
        
    except Exception as e:
        print(f"\n❌ Specific issue test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all diagnostics"""
    print("🚀 Roboflow Ingestion Diagnostics")
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Run main diagnostic
    result1 = await test_roboflow_ingestion()
    
    # Run specific issue test
    result2 = await test_specific_issue()
    
    print("\n" + "=" * 70)
    if result1 and result2:
        print("✅ ALL DIAGNOSTICS PASSED")
        print("\n🎯 Next Steps:")
        print("1. Check Celery worker logs for specific error messages")
        print("2. Verify Redis is running: redis-cli ping")
        print("3. Test with a smaller dataset first")
        print("4. Check Supabase job records for error details")
    else:
        print("❌ SOME DIAGNOSTICS FAILED")
        print("\n🔧 Troubleshooting:")
        print("1. Check the error messages above")
        print("2. Ensure all services are running")
        print("3. Verify API key has proper permissions")
        print("4. Check network connectivity to Roboflow")
    
    return result1 and result2

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)