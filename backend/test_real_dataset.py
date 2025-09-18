#!/usr/bin/env python3
"""
Test AI processing pipeline with real interior design dataset
"""

import asyncio
import logging
import time
from PIL import Image
import io
import sys
import os

# Add the backend path to Python path
sys.path.append('/Users/leslieisah/MDM/backend')

from app.services.ai_pipeline import process_scene_ai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_with_real_dataset():
    """Test AI pipeline with HuggingFace interior design dataset"""
    
    try:
        from datasets import load_dataset
        print("📦 Loading interior design dataset from HuggingFace...")
        
        # Load the dataset
        dataset = load_dataset("ellljoy/interior-design", split="train")
        print(f"✅ Dataset loaded: {len(dataset)} images")
        
        # Test with first few images
        test_count = min(3, len(dataset))
        print(f"🧪 Testing AI processing on {test_count} real interior scenes...")
        
        results = []
        
        for i in range(test_count):
            scene_data = dataset[i]
            print(f"\n📸 Processing image {i+1}/{test_count}...")
            
            # Get the image (use 'images' key, not 'image')
            pil_image = scene_data['images']
            prompt = scene_data.get('prompt', 'No description')
            print(f"   Image size: {pil_image.size}, mode: {pil_image.mode}")
            print(f"   Prompt: {prompt}")
            
            # Convert to bytes for processing (ensure RGB format for JPEG)
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            img_buffer = io.BytesIO()
            pil_image.save(img_buffer, format='JPEG', quality=95)
            image_data = img_buffer.getvalue()
            
            # Process through AI pipeline
            start_time = time.time()
            try:
                result = await process_scene_ai(
                    image_data=image_data,
                    scene_id=f"real_dataset_{i+1}",
                    options={}
                )
                processing_time = time.time() - start_time
                
                # Extract key results
                status = result.get('status', 'unknown')
                scene_type = result.get('scene_type', 'unknown')
                scene_conf = result.get('scene_conf', 0.0)
                objects_detected = result.get('objects_detected', 0)
                primary_style = result.get('primary_style', 'unknown')
                style_conf = result.get('style_confidence', 0.0)
                
                print(f"   ✅ Status: {status}")
                print(f"   🏠 Scene: {scene_type} (confidence: {scene_conf:.2f})")
                print(f"   🪑 Objects detected: {objects_detected}")
                print(f"   🎨 Style: {primary_style} (confidence: {style_conf:.2f})")
                print(f"   ⏱️ Processing time: {processing_time:.2f}s")
                
                results.append({
                    'image_index': i,
                    'status': status,
                    'scene_type': scene_type,
                    'scene_confidence': scene_conf,
                    'objects_detected': objects_detected,
                    'primary_style': primary_style,
                    'style_confidence': style_conf,
                    'processing_time': processing_time,
                    'success': status == 'completed'
                })
                
            except Exception as e:
                print(f"   ❌ Error processing image {i+1}: {e}")
                results.append({
                    'image_index': i,
                    'status': 'error',
                    'error': str(e),
                    'success': False
                })
        
        # Summary
        print(f"\n📊 Results Summary:")
        print("=" * 50)
        
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        print(f"✅ Successful: {len(successful)}/{len(results)}")
        print(f"❌ Failed: {len(failed)}/{len(results)}")
        
        if successful:
            avg_time = sum(r['processing_time'] for r in successful) / len(successful)
            scene_types = [r['scene_type'] for r in successful]
            styles = [r['primary_style'] for r in successful]
            total_objects = sum(r['objects_detected'] for r in successful)
            
            print(f"⏱️ Average processing time: {avg_time:.2f}s")
            print(f"🏠 Scene types detected: {', '.join(set(scene_types))}")
            print(f"🎨 Styles detected: {', '.join(set(styles))}")
            print(f"🪑 Total objects detected: {total_objects}")
        
        if failed:
            print(f"\n❌ Errors encountered:")
            for result in failed:
                if 'error' in result:
                    print(f"   Image {result['image_index']}: {result['error']}")
        
        success_rate = len(successful) / len(results) * 100
        print(f"\n🎯 Success rate: {success_rate:.1f}%")
        
        return success_rate >= 80  # 80% success rate threshold
        
    except ImportError:
        print("❌ Error: 'datasets' library not available. Install with: pip install datasets")
        return False
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_with_sample_scenes():
    """Test with sample scene types to verify classification"""
    
    print("\n🏠 Testing scene classification with sample images...")
    
    # Create different room scenes
    scenes = [
        ("Living Room", "living_room", (800, 600, "beige")),
        ("Kitchen", "kitchen", (640, 480, "white")),
        ("Bedroom", "bedroom", (800, 600, "lightblue")),
        ("Office", "office", (640, 480, "gray"))
    ]
    
    results = []
    
    for scene_name, expected_type, (width, height, color) in scenes:
        print(f"\n🖼️ Testing {scene_name}...")
        
        # Create a simple scene image
        img = Image.new('RGB', (width, height), color=color)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        
        # Add some furniture-like shapes based on room type
        if expected_type == "living_room":
            draw.rectangle([100, 200, 300, 350], fill='brown')  # Sofa
            draw.rectangle([400, 250, 500, 300], fill='tan')    # Coffee table
        elif expected_type == "kitchen":
            draw.rectangle([50, 100, 150, 400], fill='white')   # Cabinet
            draw.rectangle([200, 200, 400, 250], fill='gray')   # Counter
        elif expected_type == "bedroom":
            draw.rectangle([100, 150, 400, 350], fill='darkred')  # Bed
            draw.rectangle([450, 100, 550, 300], fill='brown')    # Dresser
        elif expected_type == "office":
            draw.rectangle([100, 200, 300, 250], fill='brown')  # Desk
            draw.rectangle([150, 150, 200, 200], fill='black')  # Chair
        
        # Convert to bytes
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=90)
        image_data = buf.getvalue()
        
        # Process
        try:
            result = await process_scene_ai(
                image_data=image_data,
                scene_id=f"sample_{expected_type}",
                options={}
            )
            
            detected_type = result.get('scene_type', 'unknown')
            confidence = result.get('scene_conf', 0.0)
            
            # Check if classification is reasonable (exact match not required)
            reasonable_matches = {
                'living_room': ['living_room', 'bedroom', 'office'],
                'kitchen': ['kitchen', 'dining_room'],
                'bedroom': ['bedroom', 'living_room'],
                'office': ['office', 'bedroom', 'living_room']
            }
            
            is_reasonable = detected_type in reasonable_matches.get(expected_type, [expected_type])
            
            print(f"   Expected: {expected_type}")
            print(f"   Detected: {detected_type} (confidence: {confidence:.2f})")
            print(f"   Result: {'✅ Reasonable' if is_reasonable else '⚠️ Unexpected'}")
            
            results.append({
                'scene_name': scene_name,
                'expected': expected_type,
                'detected': detected_type,
                'confidence': confidence,
                'reasonable': is_reasonable
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'scene_name': scene_name,
                'expected': expected_type,
                'error': str(e),
                'reasonable': False
            })
    
    # Summary
    reasonable_count = sum(1 for r in results if r.get('reasonable', False))
    print(f"\n📊 Scene Classification Test:")
    print(f"   Reasonable results: {reasonable_count}/{len(results)}")
    
    return reasonable_count >= len(results) * 0.75  # 75% reasonable threshold

async def main():
    """Run comprehensive dataset tests"""
    
    print("🚀 Testing AI Pipeline with Real Interior Design Dataset")
    print("=" * 60)
    
    # Test 1: Real dataset
    print("\n1️⃣ Testing with HuggingFace interior-design dataset...")
    real_dataset_success = await test_with_real_dataset()
    
    # Test 2: Sample scenes
    print("\n2️⃣ Testing scene classification accuracy...")
    scene_classification_success = await test_with_sample_scenes()
    
    # Overall results
    print("\n" + "=" * 60)
    print("🎯 OVERALL TEST RESULTS:")
    print(f"   Real Dataset Processing: {'✅ PASS' if real_dataset_success else '❌ FAIL'}")
    print(f"   Scene Classification: {'✅ PASS' if scene_classification_success else '❌ FAIL'}")
    
    overall_success = real_dataset_success and scene_classification_success
    print(f"\n{'🎉 ALL TESTS PASSED!' if overall_success else '⚠️ SOME TESTS FAILED'}")
    print("📝 The AI processing pipeline is ready for production dataset processing!" if overall_success else "🔧 Further tuning may be needed.")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)