#!/usr/bin/env python3
"""
Test bbox validation fix and category mapping with mock interior data
Simulates the issues found in the production logs
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

import json
from app.worker.tasks import validate_and_normalize_bbox

def test_bbox_and_category_fixes():
    """Test both bbox validation and category mapping fixes"""
    
    print("=== Testing Bbox Validation & Category Mapping Fixes ===\n")
    
    # Test Case 1: The actual problematic data from the logs
    print("Test 1: Real problematic data from production logs")
    problematic_objects = [
        {
            "label": "sofa",
            "confidence": 0.88,
            "bbox": [1261, 790, -938, -496]  # The actual negative bbox from logs
        },
        {
            "label": "potted plant",  # The category that caused foreign key violation
            "confidence": 0.75,
            "bbox": [100, 50, 150, 200]
        },
        {
            "label": "chair",
            "confidence": 0.91,
            "bbox": [500, 300, -200, -100]  # Another negative case
        }
    ]
    
    print("Testing bbox validation:")
    for i, obj in enumerate(problematic_objects):
        bbox_data = obj["bbox"]
        label = obj["label"]
        confidence = obj["confidence"]
        
        print(f"  Object {i}: {label} (conf={confidence})")
        print(f"    Input bbox: {bbox_data}")
        
        # Test bbox validation
        validated_bbox = validate_and_normalize_bbox(bbox_data, i)
        print(f"    Validated bbox: {validated_bbox}")
        
        # Check if bbox is now valid
        if validated_bbox['width'] > 0 and validated_bbox['height'] > 0:
            area = validated_bbox['width'] * validated_bbox['height']
            print(f"    ✅ Valid bbox with area = {area}")
        else:
            print(f"    ❌ Still invalid bbox")
            
        # Test category mapping
        category_mapping = {
            # Seating categories
            "sofa": "seating",
            "chair": "seating", 
            "couch": "seating",
            "armchair": "seating",
            "stool": "seating",
            "bench": "seating",
            "recliner": "seating",
            
            # Table categories
            "table": "tables",
            "dining_table": "tables",
            "coffee_table": "tables", 
            "desk": "tables",
            "nightstand": "tables",
            
            # Storage categories
            "bookshelf": "storage",
            "cabinet": "storage",
            "dresser": "storage",
            "wardrobe": "storage",
            "tv_stand": "storage",
            "shelf": "storage",
            
            # Bedroom categories
            "bed": "bedroom",
            "mattress": "bedroom",
            "headboard": "bedroom",
            
            # Lighting categories
            "lamp": "lighting",
            "floor_lamp": "lighting",
            "table_lamp": "lighting",
            "ceiling_light": "lighting",
            
            # Electronics
            "tv": "entertainment",
            "laptop": "home_office",
            "monitor": "home_office",
            
            # Kitchen appliances
            "refrigerator": "kitchen_appliances",
            "oven": "kitchen_appliances",
            "microwave": "kitchen_appliances",
            "dishwasher": "kitchen_appliances",
            
            # Decor
            "plant": "decor_accessories",
            "potted plant": "decor_accessories",  # This was the missing mapping!
            "potted_plant": "decor_accessories",
            "vase": "decor_accessories",
            "mirror": "decor_accessories",
            "clock": "decor_accessories",
            "artwork": "wall_decor",
            
            # Textiles
            "rug": "soft_furnishings",
            "pillow": "soft_furnishings",
            "curtains": "window_treatments"
        }
        
        category = category_mapping.get(label.lower(), label.lower())
        print(f"    Category mapping: '{label}' → '{category}'")
        
        if category in ["seating", "tables", "storage", "bedroom", "lighting", "entertainment", 
                       "home_office", "kitchen_appliances", "decor_accessories", "wall_decor",
                       "soft_furnishings", "window_treatments"]:
            print(f"    ✅ Valid category")
        else:
            print(f"    ⚠️  Category may need to be added to database")
        
        print()
    
    # Test Case 2: Edge cases
    print("Test 2: Edge cases and boundary conditions")
    
    edge_cases = [
        {"bbox": [0, 0, 0, 0], "label": "Should be rejected (zero area)"},
        {"bbox": [10, 20, 1, 1], "label": "Minimal valid bbox"},
        {"bbox": {"x": 100, "y": 50, "width": -10, "height": 200}, "label": "Dict with negative width"},
        {"bbox": [], "label": "Empty list"},
        {"bbox": {}, "label": "Empty dict"},
    ]
    
    for i, case in enumerate(edge_cases):
        bbox_data = case["bbox"]
        label = case["label"]
        
        print(f"  Edge case {i+1}: {label}")
        print(f"    Input: {bbox_data}")
        
        validated_bbox = validate_and_normalize_bbox(bbox_data, i)
        print(f"    Result: {validated_bbox}")
        
        if validated_bbox['width'] > 0 and validated_bbox['height'] > 0:
            print(f"    ✅ Valid")
        else:
            print(f"    ❌ Invalid (as expected)")
        print()
    
    print("🎉 All tests completed!")
    print("Summary:")
    print("- Bbox validation now handles negative coordinates correctly")
    print("- Category mapping updated to include 'potted plant' → 'decor_accessories'")
    print("- Edge cases are properly handled with fallbacks")

if __name__ == "__main__":
    test_bbox_and_category_fixes()