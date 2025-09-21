#!/usr/bin/env python3
"""
Debug segmentation data extraction from furniture-appcw dataset
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def debug_segmentation_extraction():
    """Debug segmentation data extraction step by step"""
    print("🔬 Debugging Segmentation Data Extraction")
    print("=" * 60)
    
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
    
    test_url = "https://universe.roboflow.com/vision-help/furniture-appcw"
    api_key = os.getenv("ROBOFLOW_API_KEY")
    
    print(f"🔗 Loading single image from {test_url}...")
    
    try:
        # Load just 1 image to debug
        images = service.load_roboflow_dataset_images(
            roboflow_url=test_url,
            api_key=api_key,
            export_format="coco",
            max_images=1
        )
        
        if not images:
            print("❌ No images loaded")
            return False
            
        print(f"✅ Loaded {len(images)} image")
        
        # Examine the raw data structure
        img = images[0]
        metadata = img.get('metadata', {})
        annotations = metadata.get('annotations', [])
        
        print(f"\n📸 Image Analysis:")
        print(f"   - Filename: {img.get('filename')}")
        print(f"   - Size: {img.get('width')}x{img.get('height')}")
        print(f"   - Annotations: {len(annotations)}")
        
        if annotations:
            ann = annotations[0]
            print(f"\n📦 First Annotation Raw Data:")
            print(f"   - Category: {ann.get('category')}")
            print(f"   - Confidence: {ann.get('confidence')}")
            print(f"   - BBox: {ann.get('bbox')}")
            
            # Check all keys in the annotation
            print(f"   - All keys: {list(ann.keys())}")
            
            # Check for segmentation fields
            segmentation_fields = [
                'segmentation', 'segmentation_polygon', 'segmentation_rle',
                'polygon', 'mask', 'poly'
            ]
            
            found_seg_fields = []
            for field in segmentation_fields:
                if field in ann:
                    found_seg_fields.append(field)
                    value = ann[field]
                    print(f"   ✅ Found {field}: {type(value)} - {len(value) if isinstance(value, (list, str)) else 'N/A'}")
                    
                    if field == 'segmentation' and isinstance(value, list):
                        print(f"      Polygon count: {len(value)}")
                        if value and isinstance(value[0], list):
                            print(f"      First polygon points: {len(value[0])}")
                            print(f"      Sample: {value[0][:8]}...")
            
            if not found_seg_fields:
                print(f"   ❌ No segmentation fields found")
                print(f"   📋 Available fields: {', '.join(ann.keys())}")
        
        # Test the conversion process step by step
        print(f"\n🔄 Testing Conversion Process:")
        
        # Test HuggingFace COCO conversion (what's actually being used)
        from app.services.huggingface import HuggingFaceService
        hf_service = HuggingFaceService()
        
        print(f"   Step 1: Testing COCO format detection...")
        is_coco = hf_service._is_coco_format(annotations)
        print(f"   ✅ Is COCO format: {is_coco}")
        
        print(f"   Step 2: Converting annotations...")
        converted = hf_service._convert_coco_annotations_to_modomo(annotations, "debug-scene")
        
        if converted:
            conv_obj = converted[0]
            print(f"   ✅ Converted object:")
            print(f"      - Category: {conv_obj.get('category')}")
            print(f"      - Has segmentation: {'segmentation' in conv_obj}")
            
            if 'segmentation' in conv_obj:
                seg = conv_obj['segmentation']
                print(f"      - Segmentation type: {seg.get('type')}")
                print(f"      - Data type: {type(seg.get('data'))}")
                print(f"      - Data length: {len(seg.get('data', [])) if isinstance(seg.get('data'), list) else 'N/A'}")
                
                # Show raw data structure
                print(f"   📋 Raw segmentation data: {json.dumps(seg, indent=4)[:200]}...")
        else:
            print(f"   ❌ Conversion failed")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    success = await debug_segmentation_extraction()
    print(f"\n{'✅ Debug completed' if success else '❌ Debug failed'}")
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)