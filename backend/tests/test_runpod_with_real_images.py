#!/usr/bin/env python3
"""
Test RunPod deployment with real images from R2 storage
"""

import requests
import base64
import json
import os
from dotenv import load_dotenv
from app.core.config import settings
from app.services.storage import StorageService
from app.core.supabase import init_supabase, get_supabase
import asyncio
import time

load_dotenv()

async def test_with_real_images():
    """Test RunPod with actual dataset images"""
    
    # Initialize services
    await init_supabase()
    supabase = get_supabase()
    storage = StorageService()
    
    print("🔍 Fetching scenes from database...")
    
    # Get some processed scenes
    result = supabase.table('scenes').select('*').limit(3).execute()
    
    if not result.data:
        print("❌ No scenes found in database")
        return
    
    print(f"✅ Found {len(result.data)} scenes")
    
    # RunPod endpoint
    endpoint_url = f"https://{settings.RUNPOD_ENDPOINT_ID}-8000.proxy.runpod.net/process"
    
    for scene in result.data:
        scene_id = scene['id']
        r2_key = scene.get('r2_key_original')
        
        if not r2_key:
            print(f"⚠️ Scene {scene_id[:8]} has no original image")
            continue
            
        print(f"\n📸 Processing scene {scene_id[:8]}...")
        print(f"   R2 Key: {r2_key}")
        
        try:
            # Download image from R2
            print("   Downloading from R2...")
            image_data = await storage.download_object(r2_key)
            
            if not image_data:
                print(f"   ❌ Failed to download image")
                continue
            
            # Convert to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            print(f"   Image size: {len(image_data) / 1024:.1f} KB")
            
            # Send to RunPod
            print("   Sending to RunPod AI pipeline...")
            start_time = time.time()
            
            response = requests.post(
                endpoint_url,
                json={
                    "image": image_base64,  # Changed from image_base64 to image
                    "scene_id": scene_id,
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
                
                # Check for scene analysis
                if 'scene_analysis' in result:
                    scene_info = result['scene_analysis']
                    print(f"   Scene type: {scene_info.get('scene_type', 'unknown')}")
                    print(f"   Confidence: {scene_info.get('confidence', 0):.2f}")
                else:
                    print(f"   Scene type: {result.get('scene_type', 'unknown')}")
                    print(f"   Confidence: {result.get('scene_confidence', 0):.2f}")
                
                # Objects detected
                objects = result.get('objects', [])
                print(f"   Objects detected: {len(objects)}")
                if objects:
                    for i, obj in enumerate(objects[:5]):  # Show first 5
                        print(f"      {i+1}. {obj.get('label', 'unknown')} (conf: {obj.get('confidence', 0):.2f})")
                        if 'materials' in obj:
                            print(f"         Materials: {', '.join(obj['materials'][:3])}")
                
                # Styles
                styles = result.get('styles', [])
                if styles:
                    print(f"   Styles detected:")
                    for style in styles[:3]:
                        print(f"      - {style.get('name', 'unknown')} (conf: {style.get('confidence', 0):.2f})")
                
                # Check for depth and segmentation
                has_depth = 'depth_base64' in result or 'depth_url' in result
                has_masks = any(obj.get('has_mask') for obj in objects)
                
                print(f"   Depth map: {'✅' if has_depth else '❌'}")
                print(f"   Segmentation masks: {'✅' if has_masks else '❌'}")
                
                # Compare with database values
                print(f"\n   📊 Comparison with database:")
                print(f"      DB scene type: {scene.get('scene_type', 'N/A')}")
                print(f"      AI scene type: {result.get('scene_type', 'unknown')}")
                print(f"      DB status: {scene.get('status', 'N/A')}")
                
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Request timed out")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n✨ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_with_real_images())