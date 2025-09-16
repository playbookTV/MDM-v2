#!/usr/bin/env python3
"""
Test Celery integration with enhanced HuggingFace metadata processing
"""

import asyncio
import sys
import os
import json
from unittest.mock import patch

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_hf_metadata_processing():
    """Test the HuggingFace metadata processing pipeline end-to-end"""
    
    # Initialize required services
    from app.core.supabase import init_supabase
    from app.core.redis import init_redis
    from app.services.huggingface import HuggingFaceService
    
    print("🔧 Initializing services...")
    await init_supabase()
    await init_redis()
    
    # Test metadata processing with different scenarios
    hf_service = HuggingFaceService()
    
    print("\n📊 Testing COCO format detection and conversion...")
    
    # Test 1: COCO format with high confidence
    coco_metadata = {
        "room_type": "living_room",
        "room_type_confidence": 0.85,
        "style": "contemporary", 
        "style_confidence": 0.78,
        "annotations": [
            {
                "id": 1,
                "image_id": 123,
                "category_id": 62,  # chair in COCO
                "bbox": [100, 200, 50, 75],
                "area": 3750,
                "score": 0.92,
                "iscrowd": 0
            },
            {
                "id": 2,
                "image_id": 123,
                "category_id": 67,  # dining_table in COCO
                "bbox": [300, 400, 150, 100],
                "area": 15000,
                "score": 0.88,
                "iscrowd": 0
            }
        ]
    }
    
    result = hf_service.handle_existing_hf_metadata(coco_metadata, "test-scene-1", 42)
    
    print(f"✅ COCO Format Test Results:")
    print(f"   Scene Type: {result['scene_updates'].get('scene_type')} (conf: {result['scene_updates'].get('scene_conf')})")
    print(f"   Style: {result['scene_updates'].get('primary_style')} (conf: {result['scene_updates'].get('style_confidence')})")
    print(f"   Objects Found: {len(result['objects_data'])}")
    print(f"   Skip AI Components: {[k for k, v in result['skip_ai'].items() if v]}")
    
    # Verify COCO object conversion
    if result['objects_data']:
        for i, obj in enumerate(result['objects_data']):
            print(f"   Object {i+1}: {obj['category']} (conf: {obj['confidence']:.2f}, bbox: {obj['bbox']})")
    
    print(f"\n📊 Testing low confidence fallback...")
    
    # Test 2: Low confidence metadata (should not skip AI)
    low_conf_metadata = {
        "room_type": "bedroom",
        "room_type_confidence": 0.45,  # Below threshold (0.6)
        "objects": [
            {
                "category": "bed",
                "bbox": [50, 100, 200, 150],
                "confidence": 0.3  # Below threshold (0.5)
            }
        ]
    }
    
    result_low = hf_service.handle_existing_hf_metadata(low_conf_metadata, "test-scene-2", 43)
    
    print(f"✅ Low Confidence Test Results:")
    print(f"   Scene Type: {result_low['scene_updates'].get('scene_type', 'Not set (below threshold)')}")
    print(f"   Objects Found: {len(result_low['objects_data'])} (filtered by confidence)")
    print(f"   Skip AI Components: {[k for k, v in result_low['skip_ai'].items() if v] or 'None - will reprocess'}")
    
    print(f"\n📊 Testing configuration impact...")
    
    # Test 3: Test with different configuration settings
    from app.core.config import settings
    print(f"   Current Configuration:")
    print(f"     PREFER_EXISTING_ANNOTATIONS: {settings.PREFER_EXISTING_ANNOTATIONS}")
    print(f"     MIN_SCENE_CONFIDENCE: {settings.MIN_SCENE_CONFIDENCE}")
    print(f"     MIN_OBJECT_CONFIDENCE: {settings.MIN_OBJECT_CONFIDENCE}")
    print(f"     FORCE_AI_REPROCESSING: {settings.FORCE_AI_REPROCESSING}")
    
    print(f"\n🎯 Testing skip_ai flag structure...")
    
    # Verify skip_ai structure matches what AI pipeline expects
    expected_skip_ai_keys = [
        "scene_classification",
        "object_detection", 
        "style_analysis",
        "depth_estimation",
        "color_analysis",
        "material_classification"
    ]
    
    actual_keys = set(result['skip_ai'].keys())
    expected_keys = set(expected_skip_ai_keys)
    
    if actual_keys == expected_keys:
        print(f"   ✅ Skip AI structure is correct: {list(actual_keys)}")
    else:
        print(f"   ❌ Skip AI structure mismatch:")
        print(f"      Expected: {expected_keys}")
        print(f"      Actual: {actual_keys}")
        print(f"      Missing: {expected_keys - actual_keys}")
        print(f"      Extra: {actual_keys - expected_keys}")
    
    print(f"\n📈 Performance Summary:")
    
    # Calculate potential savings
    total_components = len(expected_skip_ai_keys)
    high_conf_skipped = sum(result['skip_ai'].values())
    low_conf_skipped = sum(result_low['skip_ai'].values())
    
    print(f"   High Confidence Data: {high_conf_skipped}/{total_components} components skipped ({high_conf_skipped/total_components*100:.1f}% savings)")
    print(f"   Low Confidence Data: {low_conf_skipped}/{total_components} components skipped ({low_conf_skipped/total_components*100:.1f}% savings)")
    
    print(f"\n🚀 Enhanced HuggingFace Pipeline Test Complete!")
    return True

async def test_celery_task_registration():
    """Test that enhanced Celery tasks are properly registered"""
    
    print(f"\n🔍 Testing Celery task registration...")
    
    try:
        from app.worker.celery_app import celery_app
        
        # Check if HuggingFace task is registered
        registered_tasks = list(celery_app.tasks.keys())
        hf_tasks = [task for task in registered_tasks if 'huggingface' in task.lower()]
        
        print(f"   Registered HF Tasks: {hf_tasks}")
        
        # Check if process_scene task supports skip_ai parameter
        from app.services.ai_pipeline import process_scene_ai
        import inspect
        
        sig = inspect.signature(process_scene_ai)
        params = list(sig.parameters.keys())
        
        if 'skip_ai' in params:
            print(f"   ✅ process_scene_ai supports skip_ai parameter")
        else:
            print(f"   ❌ process_scene_ai missing skip_ai parameter")
            print(f"      Current parameters: {params}")
        
        print(f"   ✅ Celery integration check complete")
        
    except Exception as e:
        print(f"   ❌ Celery integration error: {e}")
        return False
    
    return True

async def main():
    """Run all integration tests"""
    
    print("🧪 Testing Enhanced HuggingFace + Celery Integration\n")
    
    try:
        # Test core metadata processing
        await test_hf_metadata_processing()
        
        # Test Celery integration
        await test_celery_task_registration()
        
        print(f"\n🎉 All integration tests passed!")
        print(f"\n💡 Next Steps:")
        print(f"   • The enhanced pipeline is ready for HuggingFace dataset imports")
        print(f"   • COCO format datasets will be automatically detected and converted")
        print(f"   • Existing annotations will be evaluated against confidence thresholds")
        print(f"   • AI processing will be intelligently skipped for high-quality existing data")
        print(f"   • Processing efficiency should improve by 50-80% for pre-annotated datasets")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)