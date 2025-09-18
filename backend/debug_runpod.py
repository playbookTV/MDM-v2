#!/usr/bin/env python3

import asyncio
import logging
import requests
import base64
import json
from PIL import Image
import io

# Configure logging to see the actual error
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

def create_test_image():
    """Create a simple test image"""
    img = Image.new('RGB', (640, 480), color='red')
    
    # Add some simple objects for detection
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([100, 100, 200, 200], fill='blue')  # Simple square
    draw.rectangle([300, 200, 450, 350], fill='green')  # Another square
    
    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=95)
    return buf.getvalue()

def test_runpod_direct():
    """Test RunPod endpoint directly with HTTP request"""
    
    # Create test image
    image_data = create_test_image()
    image_b64 = base64.b64encode(image_data).decode('utf-8')
    
    # Prepare payload (simplified)
    payload = {
        "image": image_b64,
        "scene_id": "debug_direct",
        "options": {}
    }
    
    # Send request
    endpoint_url = "https://v92kcxqhcn8gst-8000.proxy.runpod.net/process"
    
    print(f"Sending request to: {endpoint_url}")
    print(f"Image size: {len(image_data)} bytes")
    
    try:
        response = requests.post(
            endpoint_url,
            json=payload,
            timeout=60,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("Response Keys:", list(result.keys()))
            
            if result.get("status") == "success":
                print("✅ Success!")
                print("Objects detected:", result.get("result", {}).get("objects_detected", 0))
            else:
                print("❌ Error:", result.get("error"))
                print("Full response:", json.dumps(result, indent=2))
        else:
            print("❌ HTTP Error")
            print("Response text:", response.text[:500])
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_runpod_direct()