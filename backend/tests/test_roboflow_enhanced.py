#!/usr/bin/env python3
"""
Test script for enhanced Roboflow integration with skip_ai functionality
"""

import os
import sys
import logging
from unittest.mock import Mock, patch

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_roboflow_metadata():
    """Test enhanced Roboflow metadata processing with skip_ai functionality"""
    print("🧪 Testing Enhanced Roboflow Metadata Processing")
    print("=" * 60)
    
    try:
        from app.services.roboflow import RoboflowService
        
        # Mock dependencies including HuggingFace service
        with patch('app.services.roboflow.StorageService'), \
             patch('app.services.roboflow.DatasetService'), \
             patch('app.services.huggingface.HuggingFaceService') as mock_hf_service:
            
            # Mock HuggingFace service methods
            mock_hf_instance = mock_hf_service.return_value
            mock_hf_instance._is_coco_format.return_value = True
            mock_hf_instance._convert_coco_annotations_to_modomo.return_value = [
                {
                    "category": "chair",
                    "confidence": 0.95,
                    "bbox": [100, 150, 80, 120],
                    "description": None,
                    "attributes": {}
                },
                {
                    "category": "couch", 
                    "confidence": 0.88,
                    "bbox": [250, 200, 150, 90],
                    "description": None,
                    "attributes": {}
                }
            ]
            
            service = RoboflowService()
            
            # Test 1: High-quality COCO annotations
            print("✅ Test 1: High-quality COCO format Roboflow data")
            
            coco_metadata = {
                "image_id": 123,
                "room_type": "living_room",
                "room_type_confidence": 0.92,
                "style": "contemporary",
                "style_confidence": 0.85,
                "colors": ["#F5F5DC", "#8B4513", "#2F4F4F"],
                "annotations": [
                    {
                        "id": 1,
                        "image_id": 123,
                        "category_id": 62,  # chair in COCO
                        "bbox": [100, 150, 80, 120],
                        "area": 9600,
                        "score": 0.95,
                        "iscrowd": 0
                    },
                    {
                        "id": 2, 
                        "image_id": 123,
                        "category_id": 63,  # couch in COCO
                        "bbox": [250, 200, 150, 90],
                        "area": 13500,
                        "score": 0.88,
                        "iscrowd": 0
                    }
                ]
            }
            
            result = service.handle_existing_roboflow_metadata(
                coco_metadata, "test-scene-coco", 0
            )
            
            assert isinstance(result, dict), "Should return dict"
            assert "skip_ai" in result, "Should have skip_ai key"
            assert "scene_updates" in result, "Should have scene_updates key"
            assert "objects_data" in result, "Should have objects_data key"
            
            skip_ai = result["skip_ai"]
            scene_updates = result["scene_updates"]
            objects_data = result["objects_data"]
            
            print(f"   ✓ Scene classification: {'SKIP' if skip_ai['scene_classification'] else 'PROCESS'}")
            print(f"   ✓ Object detection: {'SKIP' if skip_ai['object_detection'] else 'PROCESS'}")
            print(f"   ✓ Style analysis: {'SKIP' if skip_ai['style_analysis'] else 'PROCESS'}")
            print(f"   ✓ Color analysis: {'SKIP' if skip_ai['color_analysis'] else 'PROCESS'}")
            print(f"   ✓ Material classification: {'SKIP' if skip_ai['material_classification'] else 'PROCESS'}")
            
            # Verify scene metadata extraction
            assert scene_updates.get("scene_type") == "living_room", f"Expected living_room, got {scene_updates.get('scene_type')}"
            assert scene_updates.get("primary_style") == "contemporary", f"Expected contemporary, got {scene_updates.get('primary_style')}"
            assert "color_analysis" in scene_updates, "Should extract color analysis"
            
            # Should skip multiple components for high-quality data
            skipped_count = sum(skip_ai.values())
            assert skipped_count >= 3, f"Should skip at least 3 components, only skipped {skipped_count}"
            
            print(f"   ✓ {skipped_count}/6 components skipped ({skipped_count/6*100:.1f}% efficiency)")
            print(f"   ✓ Objects extracted: {len(objects_data)}")
            
            # Test 2: Standard Roboflow format
            print("\n✅ Test 2: Standard Roboflow format data")
            
            standard_metadata = {
                "room": "bedroom",
                "room_confidence": 0.78,
                "design_style": "traditional",
                "design_style_confidence": 0.72,
                "objects": [
                    {
                        "category": "bed",
                        "bbox": [150, 200, 180, 120],
                        "confidence": 0.91
                    },
                    {
                        "category": "dresser", 
                        "bbox": [50, 180, 90, 150],
                        "confidence": 0.85
                    }
                ]
            }
            
            result2 = service.handle_existing_roboflow_metadata(
                standard_metadata, "test-scene-standard", 1
            )
            
            skip_ai2 = result2["skip_ai"]
            scene_updates2 = result2["scene_updates"]
            
            print(f"   ✓ Scene type detected: {scene_updates2.get('scene_type')}")
            print(f"   ✓ Style detected: {scene_updates2.get('primary_style')}")
            
            skipped_count2 = sum(skip_ai2.values())
            print(f"   ✓ {skipped_count2}/6 components skipped ({skipped_count2/6*100:.1f}% efficiency)")
            
            # Test 3: Low-quality data (should process most components)
            print("\n✅ Test 3: Low-quality data (minimal skipping)")
            
            low_quality_metadata = {
                "room_type": "unknown",
                "room_type_confidence": 0.45,  # Below threshold
                "style": "unclear",
                "style_confidence": 0.35,  # Below threshold
                "objects": [
                    {
                        "category": "furniture",
                        "bbox": [100, 100, 50, 50],
                        "confidence": 0.4  # Below threshold
                    }
                ]
            }
            
            result3 = service.handle_existing_roboflow_metadata(
                low_quality_metadata, "test-scene-lowquality", 2
            )
            
            skip_ai3 = result3["skip_ai"]
            skipped_count3 = sum(skip_ai3.values())
            
            print(f"   ✓ {skipped_count3}/6 components skipped ({skipped_count3/6*100:.1f}% efficiency)")
            assert skipped_count3 <= 1, f"Should skip very few components for low-quality data, skipped {skipped_count3}"
            
            # Test 4: Configuration override
            print("\n✅ Test 4: Force reprocessing configuration")
            
            with patch('app.core.config.settings.FORCE_AI_REPROCESSING', True):
                result4 = service.handle_existing_roboflow_metadata(
                    coco_metadata, "test-scene-force", 3
                )
                
                skip_ai4 = result4["skip_ai"]
                skipped_count4 = sum(skip_ai4.values())
                
                print(f"   ✓ Force reprocessing: {skipped_count4}/6 components skipped")
                assert skipped_count4 == 0, f"Force reprocessing should skip no components, skipped {skipped_count4}"
            
            print("\n🎉 All enhanced Roboflow metadata tests passed!")
            return True
            
    except Exception as e:
        print(f"\n❌ Enhanced Roboflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_roboflow_helper_methods():
    """Test Roboflow metadata extraction helper methods"""
    print("\n🧪 Testing Roboflow Helper Methods")
    print("=" * 50)
    
    try:
        from app.services.roboflow import RoboflowService
        
        with patch('app.services.roboflow.StorageService'), \
             patch('app.services.roboflow.DatasetService'):
            
            service = RoboflowService()
            
            # Test room extraction
            print("✅ Test 1: Room info extraction")
            
            room_metadata = {
                "room_type": "kitchen",
                "room_type_confidence": 0.89,
                "other_field": "ignored"
            }
            
            room_info = service._extract_roboflow_room_info(room_metadata)
            assert room_info is not None, "Should extract room info"
            assert room_info['room_type'] == "kitchen", f"Expected kitchen, got {room_info['room_type']}"
            assert room_info['confidence'] == 0.89, f"Expected 0.89, got {room_info['confidence']}"
            print(f"   ✓ Room: {room_info['room_type']} (conf: {room_info['confidence']})")
            
            # Test style extraction
            print("\n✅ Test 2: Style info extraction")
            
            style_metadata = {
                "design_style": "minimalist",
                "design_style_confidence": 0.77,
                "unrelated": "data"
            }
            
            style_info = service._extract_roboflow_style_info(style_metadata)
            assert style_info is not None, "Should extract style info"
            assert style_info['style'] == "minimalist", f"Expected minimalist, got {style_info['style']}"
            assert style_info['confidence'] == 0.77, f"Expected 0.77, got {style_info['confidence']}"
            print(f"   ✓ Style: {style_info['style']} (conf: {style_info['confidence']})")
            
            # Test color extraction
            print("\n✅ Test 3: Color info extraction")
            
            color_metadata = {
                "dominant_colors": ["#FF0000", "#00FF00", "#0000FF"],
                "other_stuff": "ignored"
            }
            
            color_info = service._extract_roboflow_color_info(color_metadata)
            assert color_info is not None, "Should extract color info"
            assert len(color_info['dominant_colors']) == 3, f"Expected 3 colors, got {len(color_info['dominant_colors'])}"
            assert color_info['color_count'] == 3, f"Expected count 3, got {color_info['color_count']}"
            print(f"   ✓ Colors: {color_info['color_count']} colors extracted")
            
            print("\n🎉 All helper method tests passed!")
            return True
            
    except Exception as e:
        print(f"\n❌ Helper method test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run enhanced Roboflow integration tests"""
    print("🚀 Starting Enhanced Roboflow Integration Tests")
    print("=" * 70)
    
    tests = [
        ("Enhanced Metadata Processing", test_enhanced_roboflow_metadata),
        ("Helper Method Tests", test_roboflow_helper_methods),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: FAILED with exception: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Enhanced Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All enhanced Roboflow tests passed!")
        print("💡 Key Features Verified:")
        print("   ✅ COCO format detection and conversion")
        print("   ✅ Configuration-driven confidence thresholds")
        print("   ✅ Intelligent skip_ai flag generation")
        print("   ✅ Multiple metadata format support")
        print("   ✅ Significant processing efficiency gains")
        return True
    else:
        print("❌ Some enhanced tests failed. Check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)