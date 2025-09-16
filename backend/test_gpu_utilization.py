#!/usr/bin/env python3
"""
Test script to verify GPU utilization in RunPod handler
"""

import json
import base64
from PIL import Image
import io

# Import the handler
from handler_fixed import handler, check_gpu_utilization

def create_test_image():
    """Create a simple test image"""
    # Create a 512x512 RGB image
    img = Image.new('RGB', (512, 512), color='white')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return img_b64

def test_gpu_check():
    """Test GPU diagnostics"""
    print("🔍 Testing GPU diagnostics...")
    
    event = {
        "input": {
            "gpu_check": True
        }
    }
    
    result = handler(event)
    print(f"GPU Check Result: {json.dumps(result, indent=2)}")
    return result

def test_health_check():
    """Test health check with GPU info"""
    print("🏥 Testing health check...")
    
    event = {
        "input": {
            "health_check": True
        }
    }
    
    result = handler(event)
    print(f"Health Check Result: {json.dumps(result, indent=2)}")
    return result

def test_image_processing():
    """Test actual image processing to verify GPU usage"""
    print("🖼️ Testing image processing...")
    
    test_image = create_test_image()
    
    event = {
        "input": {
            "image": test_image,
            "scene_id": "test_gpu_utilization"
        }
    }
    
    # Get GPU status before processing
    print("GPU status before processing:")
    gpu_before = check_gpu_utilization()
    print(json.dumps(gpu_before, indent=2))
    
    # Process image
    result = handler(event)
    
    # Get GPU status after processing
    print("\nGPU status after processing:")
    gpu_after = check_gpu_utilization()
    print(json.dumps(gpu_after, indent=2))
    
    # Check if processing was successful
    if result.get("status") == "success":
        print("✅ Image processing successful!")
        processing_time = result.get("result", {}).get("processing_time", 0)
        objects_detected = result.get("result", {}).get("objects_detected", 0)
        scene_type = result.get("result", {}).get("scene_analysis", {}).get("scene_type", "unknown")
        
        print(f"   Processing time: {processing_time}s")
        print(f"   Objects detected: {objects_detected}")
        print(f"   Scene type: {scene_type}")
        
        # Check for GPU memory increase (indicating GPU usage)
        if gpu_before.get("gpu_available") and gpu_after.get("gpu_available"):
            memory_before = gpu_before["devices"][0]["memory_used_mb"]
            memory_after = gpu_after["devices"][0]["memory_used_mb"]
            memory_diff = memory_after - memory_before
            
            if memory_diff > 0:
                print(f"✅ GPU memory increased by {memory_diff}MB (models loaded on GPU)")
            else:
                print(f"⚠️ No significant GPU memory change detected")
    else:
        print(f"❌ Image processing failed: {result.get('error', 'Unknown error')}")
    
    return result

def main():
    """Run all GPU utilization tests"""
    print("🚀 Starting GPU utilization tests for RunPod handler\n")
    
    try:
        # Test 1: GPU diagnostics
        test_gpu_check()
        print("\n" + "="*50 + "\n")
        
        # Test 2: Health check
        test_health_check()
        print("\n" + "="*50 + "\n")
        
        # Test 3: Image processing
        test_image_processing()
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()