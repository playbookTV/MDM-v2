#!/usr/bin/env python3
"""
Test script for bbox validation and normalization
"""
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.worker.tasks import validate_and_normalize_bbox

def test_bbox_validation():
    """Test cases for bbox validation"""
    
    print("=== Testing bbox validation and normalization ===\n")
    
    # Test case 1: Valid [x,y,w,h] format
    print("Test 1: Valid [x,y,w,h] format")
    bbox1 = [100, 50, 200, 150]
    result1 = validate_and_normalize_bbox(bbox1, 0)
    print(f"Input: {bbox1}")
    print(f"Output: {result1}")
    assert result1 == {'x': 100, 'y': 50, 'width': 200, 'height': 150}
    print("✅ PASS\n")
    
    # Test case 2: Negative dimensions (the problematic case from DB)
    print("Test 2: Negative dimensions [x1,y1,x2,y2] disguised as [x,y,w,h]")
    bbox2 = [1261, 790, -938, -496]  # The actual problematic data from DB
    result2 = validate_and_normalize_bbox(bbox2, 1)
    print(f"Input: {bbox2}")
    print(f"Output: {result2}")
    # Should convert x1=1261, y1=790, x2=-938, y2=-496 
    # But x2 < x1 and y2 < y1, so swap: x1=-938, y1=-496, x2=1261, y2=790
    # Then: x=-938, y=-496, w=1261-(-938)=2199, h=790-(-496)=1286
    # But x,y should be non-negative, so x=0, y=0
    expected_width = 1261 - (-938)  # 2199
    expected_height = 790 - (-496)   # 1286
    assert result2['x'] == 0 and result2['y'] == 0  # Clamped to non-negative
    assert result2['width'] == expected_width and result2['height'] == expected_height
    print("✅ PASS\n")
    
    # Test case 3: Dict format with valid data
    print("Test 3: Dict format with valid data")
    bbox3 = {'x': 50, 'y': 25, 'width': 100, 'height': 75}
    result3 = validate_and_normalize_bbox(bbox3, 2)
    print(f"Input: {bbox3}")
    print(f"Output: {result3}")
    assert result3 == {'x': 50, 'y': 25, 'width': 100, 'height': 75}
    print("✅ PASS\n")
    
    # Test case 4: Dict format with negative/zero dimensions
    print("Test 4: Dict format with invalid dimensions")
    bbox4 = {'x': 10, 'y': 20, 'width': 0, 'height': -5}
    result4 = validate_and_normalize_bbox(bbox4, 3)
    print(f"Input: {bbox4}")
    print(f"Output: {result4}")
    assert result4 == {'x': 0, 'y': 0, 'width': 0, 'height': 0}
    print("✅ PASS\n")
    
    # Test case 5: Invalid format
    print("Test 5: Invalid format (empty dict)")
    bbox5 = {}
    result5 = validate_and_normalize_bbox(bbox5, 4)
    print(f"Input: {bbox5}")
    print(f"Output: {result5}")
    assert result5 == {'x': 0, 'y': 0, 'width': 0, 'height': 0}
    print("✅ PASS\n")
    
    # Test case 6: Another negative case similar to real data
    print("Test 6: Another negative dimensions case")
    bbox6 = [500, 300, -200, -100]
    result6 = validate_and_normalize_bbox(bbox6, 5)
    print(f"Input: {bbox6}")
    print(f"Output: {result6}")
    # x1=500, y1=300, x2=-200, y2=-100
    # After swapping: x1=-200, y1=-100, x2=500, y2=300  
    # x=0 (clamped), y=0 (clamped), w=500-(-200)=700, h=300-(-100)=400
    assert result6['x'] == 0 and result6['y'] == 0
    assert result6['width'] == 700 and result6['height'] == 400
    print("✅ PASS\n")
    
    print("🎉 All tests passed! Bbox validation is working correctly.")

if __name__ == "__main__":
    test_bbox_validation()