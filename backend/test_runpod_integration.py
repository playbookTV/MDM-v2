#!/usr/bin/env python3
"""
Test RunPod Integration
Test script to verify RunPod AI processing is working correctly
"""

import base64
import asyncio
import sys
import os
from pathlib import Path

# Add the backend app to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.runpod_client import RunPodClient
from app.core.config import settings

async def test_runpod_health_check():
    """Test RunPod endpoint health check"""
    print("🔍 Testing RunPod health check...")
    
    client = RunPodClient()
    
    # Test health check
    result = await client.health_check()
    
    if result.get("success"):
        print("✅ RunPod health check passed!")
        print(f"   Status: {result['response'].get('status')}")
        print(f"   Models loaded: {result['response'].get('models_loaded')}")
        print(f"   Available models: {result['response'].get('available_models')}")
        return True
    else:
        print("❌ RunPod health check failed!")
        print(f"   Error: {result.get('error')}")
        return False

async def test_runpod_image_processing():
    """Test RunPod with a simple test image"""
    print("🖼️  Testing RunPod image processing...")
    
    # Create a simple test image (1x1 pixel RGB)
    from PIL import Image
    import io
    
    # Create a simple test image
    test_image = Image.new('RGB', (100, 100), color='blue')
    
    # Convert to base64
    img_buffer = io.BytesIO()
    test_image.save(img_buffer, format='JPEG')
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    client = RunPodClient()
    
    # Test image processing
    result = await client.process_scene(
        image_data=img_base64,
        scene_id="test_scene_001",
        options={}
    )
    
    if result.get("success"):
        print("✅ RunPod image processing successful!")
        response = result['response']
        print(f"   Processing time: {response.get('processing_time')}s")
        if 'scene_analysis' in response:
            scene = response['scene_analysis']
            print(f"   Scene type: {scene.get('scene_type')} (confidence: {scene.get('confidence'):.2f})")
        if 'objects' in response:
            print(f"   Objects detected: {len(response['objects'])}")
        if 'style_analysis' in response:
            style = response['style_analysis']
            print(f"   Primary style: {style.get('primary_style')} (confidence: {style.get('style_confidence'):.2f})")
        return True
    else:
        print("❌ RunPod image processing failed!")
        print(f"   Error: {result.get('error')}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting RunPod Integration Tests\n")
    
    print(f"📋 Configuration:")
    print(f"   API Key: {'***' + settings.RUNPOD_API_KEY[-8:] if settings.RUNPOD_API_KEY else 'Not set'}")
    print(f"   Endpoint ID: {settings.RUNPOD_ENDPOINT_ID or 'Not set'}")
    print(f"   Endpoint URL: {settings.RUNPOD_ENDPOINT_URL or 'Not set'}")
    print(f"   AI Processing Enabled: {settings.AI_PROCESSING_ENABLED}")
    print(f"   Use Local AI: {settings.USE_LOCAL_AI}")
    print()
    
    if not settings.RUNPOD_API_KEY or not settings.RUNPOD_ENDPOINT_ID:
        print("❌ RunPod configuration missing! Please check your .env file.")
        return False
    
    # Test 1: Health Check
    health_ok = await test_runpod_health_check()
    print()
    
    if not health_ok:
        print("⚠️  Health check failed, skipping image processing test")
        return False
    
    # Test 2: Image Processing
    processing_ok = await test_runpod_image_processing()
    print()
    
    if health_ok and processing_ok:
        print("🎉 All RunPod integration tests passed!")
        print("✨ Your AI pipeline is ready for production!")
        return True
    else:
        print("❌ Some tests failed. Please check the RunPod configuration.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)