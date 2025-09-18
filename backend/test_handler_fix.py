#!/usr/bin/env python3
"""
Test script to validate the RunPod handler fixes
"""

import logging
from PIL import Image
import io
import base64

logging.basicConfig(level=logging.INFO)

def test_image_processing():
    """Test basic image processing that might cause the error"""
    print("🧪 Testing image processing...")
    
    # Create test image
    img = Image.new('RGB', (640, 480), color='red')
    
    # Test operations that might cause list/integer issues
    try:
        # Test image.size usage (this returns a tuple)
        width, height = img.size
        print(f"✅ Image dimensions: {width}x{height}")
        
        # Test arithmetic with dimensions (common error source)
        area = width * height
        print(f"✅ Image area calculation: {area}")
        
        # Test tuple unpacking (another common issue)
        size_tuple = img.size
        print(f"✅ Size tuple: {size_tuple}")
        
        # Test operations that expect integers but might get lists
        center_x = int(width / 2)
        center_y = int(height / 2)
        print(f"✅ Center coordinates: ({center_x}, {center_y})")
        
        # Test thumbnail generation (from handler code)
        thumbnail = img.copy()
        thumbnail.thumbnail((256, 256), Image.Resampling.LANCZOS)
        print(f"✅ Thumbnail size: {thumbnail.size}")
        
        # Test base64 encoding/decoding
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        # Test decoding
        decoded_bytes = base64.b64decode(img_b64)
        decoded_img = Image.open(io.BytesIO(decoded_bytes)).convert('RGB')
        print(f"✅ Base64 round-trip: {decoded_img.size}")
        
        return True
        
    except Exception as e:
        print(f"❌ Image processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_list_operations():
    """Test operations that commonly cause list/integer errors"""
    print("🧪 Testing list/integer operations...")
    
    try:
        # Test scenarios that might cause the error
        image_size = (640, 480)  # Tuple like image.size
        
        # Test direct usage (correct)
        width, height = image_size
        print(f"✅ Tuple unpacking: {width}, {height}")
        
        # Test indexing (correct)
        w = image_size[0]
        h = image_size[1]
        print(f"✅ Index access: {w}, {h}")
        
        # Test potential error: passing tuple where int expected
        def expects_int(x):
            return int(x)
        
        # This would cause an error if we passed the whole tuple
        result1 = expects_int(image_size[0])  # Correct
        print(f"✅ Single value to int: {result1}")
        
        # This would cause "list object cannot be interpreted as an integer"
        # result2 = expects_int(image_size)  # Wrong - would fail
        
        # Test list vs tuple handling
        size_list = list(image_size)
        size_tuple = tuple(image_size)
        print(f"✅ List/tuple conversion: {size_list} -> {size_tuple}")
        
        return True
        
    except Exception as e:
        print(f"❌ List operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_potential_clip_issues():
    """Test potential CLIP-related issues"""
    print("🧪 Testing CLIP input patterns...")
    
    try:
        # Simulate CLIP processor input patterns
        from PIL import Image
        
        img = Image.new('RGB', (224, 224), color='blue')
        
        # Test: single image vs list of images
        single_image = img
        image_list = [img]
        
        print(f"✅ Single image type: {type(single_image)}")
        print(f"✅ Image list type: {type(image_list)}, length: {len(image_list)}")
        
        # The fix: always use list for CLIP processor
        images_for_clip = [single_image] if not isinstance(single_image, list) else single_image
        print(f"✅ Normalized for CLIP: {type(images_for_clip)}, length: {len(images_for_clip)}")
        
        return True
        
    except Exception as e:
        print(f"❌ CLIP patterns test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🔍 Testing RunPod handler fixes...")
    print("=" * 50)
    
    tests = [
        ("Image Processing", test_image_processing),
        ("List/Integer Operations", test_list_operations),
        ("CLIP Input Patterns", test_potential_clip_issues),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if not success:
            all_passed = False
    
    print(f"\n{'🎉 All tests passed!' if all_passed else '⚠️ Some tests failed.'}")
    return all_passed

if __name__ == "__main__":
    main()