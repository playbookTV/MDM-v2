#!/usr/bin/env python3
"""
Test script for RunPod AI Pipeline
Run this to verify your models are working correctly
"""

import requests
import base64
import json
import time
import io
from PIL import Image
import numpy as np

def create_test_image():
    """Create a simple test image for testing"""
    # Create a 512x512 test image with some basic shapes
    img = Image.new('RGB', (512, 512), color='white')
    
    # Draw a simple room-like scene
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Floor
    draw.rectangle([0, 300, 512, 512], fill='#8B4513')
    
    # Wall
    draw.rectangle([0, 0, 512, 300], fill='#F5F5DC')
    
    # Window
    draw.rectangle([100, 50, 200, 150], fill='#87CEEB')
    
    # Door
    draw.rectangle([400, 200, 500, 512], fill='#8B4513')
    
    # Simple furniture (table)
    draw.rectangle([150, 350, 350, 380], fill='#8B4513')
    draw.rectangle([140, 380, 360, 450], fill='#8B4513')
    
    return img

def test_runpod_endpoint(endpoint_url: str, api_key: str = None):
    """Test the RunPod endpoint with a sample image"""
    
    # Create test image
    test_img = create_test_image()
    
    # Convert to base64
    img_buffer = io.BytesIO()
    test_img.save(img_buffer, format='JPEG')
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    # Prepare request
    headers = {
        "Content-Type": "application/json"
    }
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    payload = {
        "input": {
            "image": img_base64
        }
    }
    
    print("🚀 Testing RunPod AI Pipeline...")
    print(f"Endpoint: {endpoint_url}")
    print(f"Image size: {test_img.size}")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            endpoint_url,
            headers=headers,
            json=payload,
            timeout=120  # 2 minutes timeout for AI processing
        )
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Processing time: {processing_time:.2f}s")
            
            # Display results
            if result.get("status") == "success":
                ai_result = result.get("result", {})
                
                print(f"\n📊 AI Analysis Results:")
                print(f"Scene Type: {ai_result.get('scene_analysis', {}).get('scene_type', 'Unknown')}")
                print(f"Scene Confidence: {ai_result.get('scene_analysis', {}).get('confidence', 0):.2f}")
                print(f"Objects Detected: {len(ai_result.get('objects', []))}")
                
                # Show object details
                for i, obj in enumerate(ai_result.get('objects', [])[:5]):  # Show first 5
                    print(f"  {i+1}. {obj.get('category', 'Unknown')} "
                          f"(conf: {obj.get('confidence', 0):.2f})")
                
                if ai_result.get('depth_map'):
                    print(f"Depth Map: Generated ({len(ai_result['depth_map'])} bytes)")
                
            else:
                print(f"❌ AI processing failed: {result.get('error', 'Unknown error')}")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (AI processing taking too long)")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_local_models():
    """Test if models can be loaded locally (for debugging)"""
    print("🔍 Testing local model loading...")
    
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
        print(f"✅ CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
            print(f"✅ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        
        # Test basic imports
        try:
            from ultralytics import YOLO
            print("✅ YOLO: Available")
        except ImportError:
            print("❌ YOLO: Not available")
            
        try:
            from segment_anything import SamPredictor
            print("✅ SAM2: Available")
        except ImportError:
            print("❌ SAM2: Not available")
            
        try:
            import clip
            print("✅ CLIP: Available")
        except ImportError:
            print("❌ CLIP: Not available")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")

if __name__ == "__main__":
    print("🧪 RunPod AI Pipeline Test Suite")
    print("=" * 50)
    
    # Test 1: Local model availability
    test_local_models()
    
    print("\n" + "=" * 50)
    
    # Test 2: RunPod endpoint (if configured)
    endpoint_url = input("\nEnter your RunPod endpoint URL (or press Enter to skip): ").strip()
    
    if endpoint_url:
        api_key = input("Enter your RunPod API key (or press Enter if not required): ").strip()
        test_runpod_endpoint(endpoint_url, api_key if api_key else None)
    else:
        print("⏭️ Skipping endpoint test")
    
    print("\n🎯 Next steps:")
    print("1. Deploy to RunPod: ./deploy-runpod.sh")
    print("2. Test with real images")
    print("3. Monitor performance and costs")
