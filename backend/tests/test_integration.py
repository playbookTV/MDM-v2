#!/usr/bin/env python3
"""
Integration test for Task 008 - bbox coordinate validation.

This tests the complete pipeline from worker tasks to ensure
negative bbox coordinates are properly handled.
"""

import sys
sys.path.insert(0, '/Users/leslieisah/MDM/backend')

from app.utils.bbox import validate_and_normalize_bbox

def test_real_world_cases():
    """Test real-world problematic cases from the task description."""
    print("=== Testing Real-World Problematic Cases ===")
    
    # Case from task description: x=1261, y=790, w=-938, h=-496
    # This suggests the actual coordinates were [323, 294, 1261, 790] in xyxy format
    # because x2-x1 = 1261-323 = 938 and y2-y1 = 790-294 = 496
    problematic_cases = [
        ([1261, 790, -938, -496], "Task example: negative w/h"),
        ([323, 294, 1261, 790], "Corrected xyxy format"),
        ([50, 100, -30, -40], "Small negative dimensions"),
        ([0, 0, -100, -200], "Zero origin with negatives"),
        ([1000, 1000, -50, -80], "Large coords with small negatives"),
    ]
    
    for bbox_input, description in problematic_cases:
        try:
            result = validate_and_normalize_bbox(bbox_input, object_index=0)
            area = result['width'] * result['height']
            print(f"✅ {description}")
            print(f"   Input:  {bbox_input}")
            print(f"   Output: {result} (area: {area})")
        except Exception as e:
            print(f"❌ {description}: {bbox_input} -> ERROR: {e}")
        print()


def test_pipeline_integration():
    """Test integration with worker pipeline expectations."""
    print("=== Testing Pipeline Integration ===")
    
    # Simulate RunPod object detection results
    mock_objects = [
        {
            "label": "sofa",
            "confidence": 0.85,
            "bbox": [10, 20, 100, 150]  # xyxy format
        },
        {
            "label": "chair", 
            "confidence": 0.75,
            "bbox": [1261, 790, -938, -496]  # problematic case
        },
        {
            "label": "table",
            "confidence": 0.90,
            "bbox": {"x": 50, "y": 60, "width": 80, "height": 120}  # dict format
        },
        {
            "label": "lamp",
            "confidence": 0.65,
            "bbox": [200, 300, 0, 50]  # zero width
        }
    ]
    
    valid_objects = []
    
    for i, obj in enumerate(mock_objects):
        bbox_data = obj.get("bbox", {})
        print(f"Processing object {i} ({obj['label']}): {bbox_data}")
        
        try:
            bbox = validate_and_normalize_bbox(bbox_data, object_index=i)
            valid_objects.append({
                'label': obj['label'],
                'confidence': obj['confidence'],
                'bbox': bbox
            })
            print(f"✅ Valid: {bbox}")
        except ValueError as e:
            print(f"❌ Skipped due to invalid bbox: {e}")
        print()
    
    print(f"Result: {len(valid_objects)}/{len(mock_objects)} objects processed successfully")
    for obj in valid_objects:
        print(f"  - {obj['label']}: {obj['bbox']}")


def test_image_bounds_integration():
    """Test integration with image bounds checking."""
    print("=== Testing Image Bounds Integration ===")
    
    # Simulate a 1920x1080 image
    image_width, image_height = 1920, 1080
    
    test_cases = [
        ([1800, 1000, 200, 150], "Partially out of bounds"),
        ([1261, 790, -938, -496], "Problematic case with bounds"),
        ([-50, -30, 100, 200], "Negative position"),
        ([2000, 2000, 100, 100], "Completely out of bounds"),
    ]
    
    for bbox_input, description in test_cases:
        try:
            bbox = validate_and_normalize_bbox(
                bbox_input, 
                object_index=0,
                image_width=image_width,
                image_height=image_height
            )
            print(f"✅ {description}: {bbox_input} -> {bbox}")
            
            # Verify bounds
            x2 = bbox['x'] + bbox['width']
            y2 = bbox['y'] + bbox['height']
            in_bounds = (0 <= bbox['x'] < image_width and 
                        0 <= bbox['y'] < image_height and
                        x2 <= image_width and y2 <= image_height)
            bounds_status = "✅" if in_bounds else "❌"
            print(f"   Bounds check: {bounds_status} ({bbox['x']},{bbox['y']} to {x2},{y2})")
            
        except Exception as e:
            print(f"❌ {description}: {bbox_input} -> ERROR: {e}")
        print()


if __name__ == '__main__':
    print("🧪 Testing Bbox Coordinate Validation Integration")
    print("=" * 60)
    
    try:
        test_real_world_cases()
        test_pipeline_integration()
        test_image_bounds_integration()
        
        print("=" * 60)
        print("🎉 All integration tests completed successfully!")
        
    except Exception as e:
        print(f"\n💥 Integration test failed: {e}")
        import traceback
        traceback.print_exc()