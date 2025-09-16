#!/usr/bin/env python3
"""
Test RunPod handler with HuggingFace interior style dataset
"""

import requests
import base64
import json
import time
from datasets import load_dataset
from PIL import Image
import io
from app.core.config import settings

def test_with_hf_dataset():
    """Test RunPod with HuggingFace interior dataset"""
    
    print("🔍 Loading HuggingFace dataset...")
    dataset = load_dataset("fatimanaik/interior_style_dataset_test_10", split="train")
    
    print(f"✅ Dataset loaded with {len(dataset)} images")
    
    # RunPod endpoint
    endpoint_url = f"https://{settings.RUNPOD_ENDPOINT_ID}-8000.proxy.runpod.net/process"
    
    # Test first 3 images
    for i in range(min(3, len(dataset))):
        item = dataset[i]
        
        print(f"\n📸 Processing image {i+1}/{min(3, len(dataset))}...")
        
        # Get image and label
        image = item['image']  # PIL Image
        label = item.get('label', 'unknown')
        
        print(f"   Dataset label: {label}")
        print(f"   Image size: {image.size}")
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        print(f"   Image data size: {len(image_bytes) / 1024:.1f} KB")
        
        # Send to RunPod
        print("   Sending to RunPod AI pipeline...")
        start_time = time.time()
        
        try:
            response = requests.post(
                endpoint_url,
                json={
                    "image": image_base64,
                    "scene_id": f"hf_test_{i}",
                    "enable_segmentation": True,
                    "enable_depth": True,
                    "enable_style": True
                },
                timeout=60
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Check if result is nested
                if 'result' in response_data:
                    result = response_data['result']
                else:
                    result = response_data
                
                print(f"   ✅ Processing successful! ({processing_time:.1f}s)")
                
                # Scene analysis
                if 'scene_analysis' in result:
                    scene_info = result['scene_analysis']
                    print(f"   Scene type: {scene_info.get('scene_type', 'unknown')}")
                    print(f"   Confidence: {scene_info.get('confidence', 0):.2f}")
                    
                    # Show alternatives if any
                    alts = scene_info.get('alternatives', [])
                    if alts:
                        print(f"   Alternatives:")
                        for alt in alts[:3]:
                            print(f"      - {alt.get('scene_type', 'unknown')}: {alt.get('confidence', 0):.2f}")
                
                # Objects detected
                objects = result.get('objects', []) or result.get('segmented_objects', [])
                print(f"   Objects detected: {len(objects)}")
                if objects:
                    print("   Objects found:")
                    for j, obj in enumerate(objects[:5]):  # Show first 5
                        label = obj.get('label', 'unknown')
                        conf = obj.get('confidence', 0)
                        print(f"      {j+1}. {label} (conf: {conf:.2f})")
                        
                        # Check materials
                        materials = obj.get('materials', [])
                        if materials:
                            print(f"         Materials: {', '.join(materials[:3])}")
                        
                        # Check description
                        desc = obj.get('description')
                        if desc:
                            print(f"         Description: {desc[:100]}...")
                
                # Style analysis
                if 'style_analysis' in result:
                    style_info = result['style_analysis']
                    print(f"   Primary style: {style_info.get('primary_style', 'unknown')}")
                    print(f"   Style confidence: {style_info.get('style_confidence', 0):.2f}")
                    
                    style_alts = style_info.get('style_alternatives', [])
                    if style_alts:
                        print(f"   Style alternatives:")
                        for style in style_alts[:3]:
                            print(f"      - {style.get('style', 'unknown')}: {style.get('confidence', 0):.2f}")
                
                # Check for depth and segmentation
                has_depth = 'depth_analysis' in result and result['depth_analysis'].get('depth_available')
                has_masks = any(obj.get('has_mask') for obj in objects)
                
                print(f"   Depth map: {'✅' if has_depth else '❌'}")
                print(f"   Segmentation masks: {'✅' if has_masks else '❌'}")
                
                # Color palette
                if 'color_palette' in result:
                    colors = result['color_palette'].get('dominant_colors', [])
                    if colors:
                        print(f"   Dominant colors: {', '.join([c['hex'] for c in colors[:3]])}")
                
                print(f"\n   📊 Comparison:")
                print(f"      Dataset label: {label}")
                if 'scene_analysis' in result:
                    print(f"      AI scene type: {result['scene_analysis'].get('scene_type', 'unknown')}")
                if 'style_analysis' in result:
                    print(f"      AI style: {result['style_analysis'].get('primary_style', 'unknown')}")
                
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Request timed out")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n✨ Test complete!")

if __name__ == "__main__":
    test_with_hf_dataset()