#!/usr/bin/env python3
"""
Test Roboflow ingestion with real dataset: https://universe.roboflow.com/sasikarn/home-ww0tg
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_real_roboflow_dataset():
    """Test with the real Roboflow dataset provided by user"""
    print("🏠 Testing Real Roboflow Dataset")
    print("=" * 70)
    print("Dataset: https://universe.roboflow.com/sasikarn/home-ww0tg")
    print("=" * 70)
    
    # Initialize services
    try:
        from app.core.supabase import init_supabase
        from app.core.redis import init_redis
        from app.services.roboflow import RoboflowService
        
        await init_supabase()
        await init_redis()
        
        service = RoboflowService()
        print("✅ Services initialized")
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False
    
    # Test dataset URL
    test_url = "https://universe.roboflow.com/sasikarn/home-ww0tg"
    api_key = os.getenv("ROBOFLOW_API_KEY")
    
    if not api_key:
        print("❌ ROBOFLOW_API_KEY not set")
        return False
    
    print(f"🔑 Using API key: {api_key[:10]}...")
    
    # Step 1: Validate URL
    print("\n🔗 Step 1: Validating URL...")
    try:
        url_parts = service.validate_roboflow_url(test_url)
        if url_parts:
            workspace, project, version = url_parts
            print(f"   ✅ URL parsed: {workspace}/{project} v{version}")
        else:
            print("   ❌ URL validation failed - trying with explicit version")
            # Try with version 1
            test_url_v1 = f"{test_url}/model/1"
            url_parts = service.validate_roboflow_url(test_url_v1)
            if url_parts:
                workspace, project, version = url_parts
                test_url = test_url_v1  # Use the versioned URL
                print(f"   ✅ URL with version parsed: {workspace}/{project} v{version}")
            else:
                print("   ❌ URL validation failed even with version")
                return False
    except Exception as e:
        print(f"   ❌ URL validation error: {e}")
        return False
    
    # Step 2: Test dataset info extraction
    print("\n📊 Step 2: Testing dataset access...")
    try:
        info = service.extract_dataset_info(test_url, api_key)
        if info:
            print(f"   ✅ Dataset accessible: {info.get('dataset_id', 'unknown')}")
            for key, value in info.items():
                print(f"      - {key}: {value}")
        else:
            print("   ❌ Dataset not accessible or invalid API key")
            print("   💡 This could mean:")
            print("      - Dataset is private and API key doesn't have access")
            print("      - Dataset doesn't exist")
            print("      - API key is invalid")
            return False
    except Exception as e:
        print(f"   ❌ Dataset access failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Test loading a few images
    print("\n🖼️  Step 3: Testing image loading...")
    try:
        print("   📥 Loading first 3 images...")
        images = service.load_roboflow_dataset_images(
            roboflow_url=test_url,
            api_key=api_key,
            export_format="coco",
            max_images=3
        )
        
        if images:
            print(f"   ✅ Successfully loaded {len(images)} images")
            for i, img in enumerate(images):
                print(f"      Image {i+1}:")
                print(f"        - Size: {img.get('width')}x{img.get('height')}")
                print(f"        - Filename: {img.get('filename', 'unknown')}")
                
                metadata = img.get('metadata', {})
                annotations = metadata.get('annotations', [])
                print(f"        - Annotations: {len(annotations)}")
                
                if annotations:
                    # Show first annotation details
                    first_ann = annotations[0]
                    print(f"        - Sample annotation: {first_ann.get('category', 'unknown')} "
                          f"(confidence: {first_ann.get('confidence', 'unknown')})")
        else:
            print("   ❌ No images loaded")
            return False
            
    except Exception as e:
        print(f"   ❌ Image loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Test metadata processing
    print("\n🔄 Step 4: Testing metadata processing...")
    if images and len(images) > 0:
        try:
            test_metadata = images[0].get('metadata', {})
            print(f"   📝 Processing metadata for first image...")
            
            result = service.handle_existing_roboflow_metadata(
                test_metadata, 
                "test-sasikarn-scene",
                0
            )
            
            print(f"   ✅ Metadata processed successfully")
            print(f"      - Scene updates: {len(result.get('scene_updates', {}))}")
            print(f"      - Objects extracted: {len(result.get('objects_data', []))}")
            
            skip_ai = result.get('skip_ai', {})
            skipped = [k for k, v in skip_ai.items() if v]
            if skipped:
                print(f"      - AI components to skip: {', '.join(skipped)}")
            else:
                print(f"      - All AI components will be processed")
                
            # Show extracted objects
            objects_data = result.get('objects_data', [])
            if objects_data:
                print(f"   📦 Object details:")
                for i, obj in enumerate(objects_data[:3]):  # Show first 3
                    print(f"      Object {i+1}: {obj.get('category')} "
                          f"(conf: {obj.get('confidence', 0):.2f}, "
                          f"bbox: {obj.get('bbox', [])})")
                          
        except Exception as e:
            print(f"   ❌ Metadata processing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Step 5: Test the full ingestion simulation
    print("\n🎯 Step 5: Simulating full ingestion...")
    print(f"   📊 Dataset Summary:")
    print(f"      - Workspace: {workspace}")
    print(f"      - Project: {project}")
    print(f"      - Version: {version}")
    print(f"      - Images tested: {len(images)}")
    print(f"      - Total annotations: {sum(len(img.get('metadata', {}).get('annotations', [])) for img in images)}")
    
    efficiency_stats = []
    for img in images:
        metadata = img.get('metadata', {})
        result = service.handle_existing_roboflow_metadata(metadata, f"test-scene-{images.index(img)}", images.index(img))
        skip_ai = result.get('skip_ai', {})
        skipped_count = sum(skip_ai.values())
        efficiency_stats.append(skipped_count)
    
    avg_efficiency = sum(efficiency_stats) / len(efficiency_stats) if efficiency_stats else 0
    print(f"      - Average AI efficiency: {avg_efficiency/6*100:.1f}% (skipping {avg_efficiency:.1f}/6 components)")
    
    print("\n✅ Real Roboflow dataset test completed successfully!")
    print("\n💡 Next steps to use this dataset:")
    print("   1. Create a dataset in the MDM system")
    print("   2. Use the Roboflow import API endpoint:")
    print(f"      POST /api/datasets/{{dataset_id}}/process-roboflow")
    print(f"      Body: {{\"roboflow_url\": \"{test_url}\"}}")
    print("   3. Monitor the job progress in the Jobs page")
    
    return True

async def main():
    """Run the real dataset test"""
    print("🚀 Real Roboflow Dataset Test")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = await test_real_roboflow_dataset()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ REAL DATASET TEST PASSED")
        print("The Roboflow ingestion should work with this dataset!")
    else:
        print("❌ REAL DATASET TEST FAILED")
        print("Check the error messages above for troubleshooting.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)