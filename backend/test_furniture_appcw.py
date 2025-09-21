#!/usr/bin/env python3
"""
Test with real Roboflow dataset: https://universe.roboflow.com/vision-help/furniture-appcw
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_furniture_appcw_dataset():
    """Test with the furniture-appcw Roboflow dataset"""
    print("🪑 Testing Furniture-APPCW Roboflow Dataset")
    print("=" * 70)
    print("Dataset: https://universe.roboflow.com/vision-help/furniture-appcw")
    print("=" * 70)
    
    # Initialize services
    try:
        from app.core.supabase import init_supabase, get_supabase
        from app.core.redis import init_redis
        from app.services.roboflow import RoboflowService
        
        await init_supabase()
        await init_redis()
        
        service = RoboflowService()
        supabase = get_supabase()
        print("✅ Services initialized")
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False
    
    # Test dataset URL
    test_url = "https://universe.roboflow.com/vision-help/furniture-appcw"
    api_key = os.getenv("ROBOFLOW_API_KEY")
    
    if not api_key:
        print("❌ ROBOFLOW_API_KEY not set")
        return False
    
    print(f"🔑 Using API key: {api_key[:10]}...")
    
    # Step 1: Validate URL and try different versions
    print("\n🔗 Step 1: Validating URL...")
    original_url = test_url
    url_parts = None
    
    # Try different version formats
    test_urls = [
        test_url,
        f"{test_url}/model/1",
        f"{test_url}/dataset/1",
        f"{test_url}/1"
    ]
    
    for url in test_urls:
        try:
            url_parts = service.validate_roboflow_url(url)
            if url_parts:
                workspace, project, version = url_parts
                test_url = url  # Use the working URL
                print(f"   ✅ URL parsed: {workspace}/{project} v{version}")
                print(f"   Using URL: {test_url}")
                break
        except Exception as e:
            continue
    
    if not url_parts:
        print("   ❌ URL validation failed for all formats")
        return False
    
    # Step 2: Test dataset access
    print("\n📊 Step 2: Testing dataset access...")
    try:
        info = service.extract_dataset_info(test_url, api_key)
        if info:
            print(f"   ✅ Dataset accessible: {info.get('dataset_id', 'unknown')}")
            for key, value in info.items():
                print(f"      - {key}: {value}")
        else:
            print("   ❌ Dataset not accessible")
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
    
    # Step 3: Test loading images and analyze enhanced data
    print("\n🖼️  Step 3: Loading images and analyzing enhanced data...")
    try:
        print("   📥 Loading first 5 images...")
        images = service.load_roboflow_dataset_images(
            roboflow_url=test_url,
            api_key=api_key,
            export_format="coco",
            max_images=5
        )
        
        if not images:
            print("   ❌ No images loaded")
            return False
            
        print(f"   ✅ Successfully loaded {len(images)} images")
        
        # Analyze enhanced data types available
        print("\n🔬 Step 4: Analyzing enhanced data types...")
        
        enhanced_features = {
            "polygon_segmentation": 0,
            "rle_segmentation": 0,
            "keypoints": 0,
            "instance_attributes": 0,
            "custom_materials": 0,
            "custom_styles": 0,
            "custom_colors": 0
        }
        
        total_annotations = 0
        all_categories = set()
        
        for i, img in enumerate(images):
            print(f"\n   📸 Image {i+1}:")
            print(f"      - Size: {img.get('width')}x{img.get('height')}")
            print(f"      - Filename: {img.get('filename', 'unknown')}")
            
            metadata = img.get('metadata', {})
            annotations = metadata.get('annotations', [])
            total_annotations += len(annotations)
            print(f"      - Annotations: {len(annotations)}")
            
            # Analyze each annotation
            for j, ann in enumerate(annotations):
                category = ann.get('category', 'unknown')
                all_categories.add(category)
                
                print(f"        📦 Object {j+1}: {category}")
                print(f"           - Confidence: {ann.get('confidence', 0):.2f}")
                print(f"           - BBox: {ann.get('bbox', [])}")
                
                # Check for enhanced features
                if 'segmentation_polygon' in ann or ('segmentation' in ann and isinstance(ann['segmentation'], list)):
                    enhanced_features["polygon_segmentation"] += 1
                    print(f"           ✅ Has polygon segmentation")
                
                if 'segmentation_rle' in ann or ('segmentation' in ann and isinstance(ann['segmentation'], dict)):
                    enhanced_features["rle_segmentation"] += 1
                    print(f"           ✅ Has RLE segmentation")
                
                if 'keypoints' in ann or 'keypoint' in ann:
                    enhanced_features["keypoints"] += 1
                    print(f"           ✅ Has keypoints")
                
                if 'attributes' in ann and ann['attributes']:
                    enhanced_features["instance_attributes"] += 1
                    print(f"           ✅ Has instance attributes: {list(ann['attributes'].keys())}")
                
                if 'material' in ann:
                    enhanced_features["custom_materials"] += 1
                    print(f"           ✅ Material: {ann['material']}")
                
                if 'style' in ann:
                    enhanced_features["custom_styles"] += 1
                    print(f"           ✅ Style: {ann['style']}")
                
                if 'color' in ann:
                    enhanced_features["custom_colors"] += 1
                    print(f"           ✅ Color: {ann['color']}")
        
        # Summary of enhanced features
        print(f"\n📊 Enhanced Data Analysis Summary:")
        print(f"   - Total images analyzed: {len(images)}")
        print(f"   - Total annotations: {total_annotations}")
        print(f"   - Unique categories: {len(all_categories)}")
        print(f"   - Categories found: {', '.join(sorted(all_categories))}")
        
        print(f"\n🔬 Enhanced Features Detection:")
        for feature, count in enhanced_features.items():
            percentage = (count / total_annotations * 100) if total_annotations > 0 else 0
            status = "✅" if count > 0 else "❌"
            print(f"   {status} {feature.replace('_', ' ').title()}: {count}/{total_annotations} ({percentage:.1f}%)")
        
        # Create a test dataset and save sample data
        print(f"\n💾 Step 5: Creating test dataset and saving sample data...")
        try:
            # Create dataset
            test_dataset = {
                "name": f"Furniture-APPCW Test {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "source_url": test_url,
                "notes": f"Real Roboflow furniture dataset test - {total_annotations} annotations, {len(all_categories)} categories"
            }
            
            result = supabase.from_("datasets").insert(test_dataset).execute()
            dataset_id = result.data[0]["id"]
            print(f"   ✅ Created test dataset: {dataset_id}")
            
            # Process first image as a sample
            if images:
                sample_img = images[0]
                
                # Upload sample image to R2
                r2_key = service.upload_image_to_r2_sync(sample_img['image'], sample_img['filename'])
                if r2_key:
                    print(f"   ✅ Uploaded sample image to R2: {r2_key}")
                    
                    # Create scene
                    scene_data = {
                        "dataset_id": dataset_id,
                        "source": sample_img['filename'],
                        "r2_key_original": r2_key,
                        "width": sample_img['width'],
                        "height": sample_img['height'],
                        "status": "processing"
                    }
                    
                    scene_result = supabase.from_("scenes").insert(scene_data).execute()
                    scene_id = scene_result.data[0]["id"]
                    print(f"   ✅ Created scene: {scene_id}")
                    
                    # Process metadata and save objects
                    metadata = sample_img.get('metadata', {})
                    result = service.handle_existing_roboflow_metadata(metadata, scene_id, 0)
                    
                    objects_created = 0
                    for obj_data in result.get('objects_data', []):
                        obj_record = {
                            "scene_id": scene_id,
                            "category_code": obj_data.get('category', 'furniture'),
                            "bbox_x": obj_data['bbox'][0] if 'bbox' in obj_data else 0,
                            "bbox_y": obj_data['bbox'][1] if 'bbox' in obj_data else 0,
                            "bbox_w": obj_data['bbox'][2] if 'bbox' in obj_data else 100,
                            "bbox_h": obj_data['bbox'][3] if 'bbox' in obj_data else 100,
                            "confidence": obj_data.get('confidence', 0.5),
                            "description": obj_data.get('description'),
                            "attrs": {
                                "real_roboflow_data": True,
                                "dataset_source": "furniture-appcw",
                                **{k: v for k, v in obj_data.items() if k not in ['category', 'bbox', 'confidence', 'description']}
                            }
                        }
                        
                        supabase.from_("objects").insert(obj_record).execute()
                        objects_created += 1
                    
                    print(f"   ✅ Created {objects_created} objects with real Roboflow data")
                    
                    # Update scene status
                    supabase.from_("scenes").update({"status": "processed"}).eq("id", scene_id).execute()
                    
                    print(f"\n💾 Test data saved:")
                    print(f"   - Dataset ID: {dataset_id}")
                    print(f"   - Scene ID: {scene_id}")
                    print(f"   - Objects: {objects_created}")
                    
        except Exception as e:
            print(f"   ⚠️ Sample data saving failed: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"   ❌ Image loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("✅ FURNITURE-APPCW DATASET TEST COMPLETED")
    
    # Determine if this dataset has enhanced features
    has_enhanced_features = any(count > 0 for count in enhanced_features.values())
    
    if has_enhanced_features:
        print("\n🎉 Enhanced Features Found!")
        print("   This dataset contains additional annotation data beyond basic bounding boxes.")
    else:
        print("\n📦 Basic Annotation Dataset")
        print("   This dataset contains standard COCO object detection annotations (bboxes + labels).")
    
    print(f"\n📋 Recommendation:")
    if has_enhanced_features:
        print("   ✅ Perfect for testing enhanced Roboflow extraction features")
        print("   ✅ Can demonstrate segmentation, keypoints, or custom attributes")
    else:
        print("   ✅ Good for testing standard object detection pipeline")
        print("   ✅ Will benefit from AI processing for missing features")
    
    return True

async def main():
    """Run the furniture-appcw dataset test"""
    print("🚀 Furniture-APPCW Dataset Analysis")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = await test_furniture_appcw_dataset()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ DATASET ANALYSIS COMPLETED")
    else:
        print("❌ DATASET ANALYSIS FAILED")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)