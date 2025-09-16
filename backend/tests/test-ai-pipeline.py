#!/usr/bin/env python3
"""
Test script for AI pipeline with RunPod integration
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ai_pipeline import process_scene_ai
from app.services.runpod_client import runpod_client
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_test_image() -> bytes:
    """Load a test image for processing"""
    test_images = [
        "test-image.jpg",
        "sample.jpg", 
        "test.png",
        "../sample-images/room.jpg"
    ]
    
    for image_path in test_images:
        if os.path.exists(image_path):
            logger.info(f"Loading test image: {image_path}")
            with open(image_path, 'rb') as f:
                return f.read()
    
    # Create a minimal test image if no test images found
    logger.warning("No test images found, creating minimal test image")
    from PIL import Image
    import io
    
    # Create a simple 512x512 RGB image
    test_img = Image.new('RGB', (512, 512), color='lightblue')
    img_bytes = io.BytesIO()
    test_img.save(img_bytes, format='JPEG')
    return img_bytes.getvalue()


async def test_configuration():
    """Test system configuration"""
    print("\n🔧 Testing Configuration...")
    
    # Test RunPod configuration
    print(f"RunPod API Key: {'✅ Set' if settings.RUNPOD_API_KEY else '❌ Missing'}")
    print(f"RunPod Endpoint ID: {'✅ Set' if settings.RUNPOD_ENDPOINT_ID else '❌ Missing'}")
    print(f"RunPod Endpoint URL: {'✅ Set' if settings.RUNPOD_ENDPOINT_URL else '❌ Missing'}")
    
    # Test AI settings
    print(f"AI Processing Enabled: {'✅ Yes' if settings.AI_PROCESSING_ENABLED else '❌ No'}")
    print(f"Use Local AI: {'✅ Yes' if settings.USE_LOCAL_AI else '❌ No'}")
    
    # Test RunPod client health
    if runpod_client.is_configured():
        health = await runpod_client.health_check()
        status = health.get('status', 'unknown')
        print(f"RunPod Health: {'✅ Healthy' if status == 'healthy' else f'❌ {status.title()}'}")
        
        if status != 'healthy':
            print(f"  Error: {health.get('message', 'Unknown error')}")
    else:
        print("RunPod Health: ❌ Not configured")


async def test_runpod_direct():
    """Test RunPod client directly"""
    if not runpod_client.is_configured():
        print("\n⚠️  RunPod not configured, skipping direct test")
        return False
    
    print("\n🚀 Testing RunPod Direct...")
    
    try:
        # Load test image
        image_data = load_test_image()
        print(f"Loaded test image: {len(image_data)} bytes")
        
        # Test direct RunPod processing
        result = await runpod_client.process_scene_runpod(
            image_data=image_data,
            scene_id="test-scene-direct",
            options={}
        )
        
        if result.get("success"):
            print("✅ RunPod direct processing successful")
            print(f"   Status: {result.get('status')}")
            if 'result' in result:
                output = result['result']
                print(f"   Objects detected: {len(output.get('objects', []))}")
                scene_analysis = output.get('scene_analysis', {})
                print(f"   Scene type: {scene_analysis.get('scene_type', 'unknown')}")
                print(f"   Confidence: {scene_analysis.get('confidence', 0.0)}")
        else:
            print(f"❌ RunPod direct processing failed: {result.get('error')}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ RunPod direct test error: {e}")
        return False


async def test_ai_pipeline():
    """Test complete AI pipeline"""
    print("\n🧠 Testing AI Pipeline...")
    
    try:
        # Load test image
        image_data = load_test_image()
        print(f"Loaded test image: {len(image_data)} bytes")
        
        # Test complete pipeline
        result = await process_scene_ai(
            image_data=image_data,
            scene_id="test-scene-pipeline",
            options={}
        )
        
        if result.get("success"):
            print("✅ AI pipeline processing successful")
            print(f"   Processed with: {result.get('processed_with', 'unknown')}")
            print(f"   Scene type: {result.get('scene_type', 'unknown')}")
            print(f"   Scene confidence: {result.get('scene_conf', 0.0)}")
            print(f"   Objects detected: {result.get('objects_detected', 0)}")
            print(f"   Primary style: {result.get('primary_style', 'unknown')}")
            print(f"   Depth available: {result.get('depth_available', False)}")
        else:
            print(f"❌ AI pipeline processing failed: {result.get('error')}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ AI pipeline test error: {e}")
        return False


async def test_performance():
    """Test processing performance"""
    print("\n⏱️  Testing Performance...")
    
    try:
        import time
        
        # Load test image
        image_data = load_test_image()
        
        # Run multiple tests
        times = []
        for i in range(3):
            start_time = time.time()
            
            result = await process_scene_ai(
                image_data=image_data,
                scene_id=f"perf-test-{i}",
                options={}
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            times.append(processing_time)
            
            status = "✅" if result.get("success") else "❌"
            print(f"  Test {i+1}: {status} {processing_time:.2f}s")
        
        if times:
            avg_time = sum(times) / len(times)
            print(f"\n📊 Performance Summary:")
            print(f"   Average time: {avg_time:.2f}s")
            print(f"   Min time: {min(times):.2f}s")
            print(f"   Max time: {max(times):.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test error: {e}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Modomo AI Pipeline Test Suite")
    print("=" * 50)
    
    results = []
    
    # Configuration test
    await test_configuration()
    
    # RunPod direct test
    runpod_success = await test_runpod_direct()
    results.append(("RunPod Direct", runpod_success))
    
    # AI pipeline test  
    pipeline_success = await test_ai_pipeline()
    results.append(("AI Pipeline", pipeline_success))
    
    # Performance test
    perf_success = await test_performance()
    results.append(("Performance", perf_success))
    
    # Summary
    print("\n📋 Test Summary:")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    # RunPod client stats
    stats = runpod_client.get_stats()
    print(f"\n🔢 RunPod Stats:")
    print(f"   Requests made: {stats['requests_made']}")
    print(f"   Success rate: {stats['success_rate_percent']}%")
    print(f"   Configured: {'Yes' if stats['configured'] else 'No'}")
    
    # Return overall success
    all_success = all(success for _, success in results)
    if all_success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check configuration and logs.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)