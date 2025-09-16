#!/usr/bin/env python3
"""
Test the enhanced HuggingFace metadata processing with skip_ai functionality
"""

import sys
import os
import logging
from unittest.mock import MagicMock, patch

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_coco_format_detection():
    """Test COCO format detection logic"""
    from app.services.huggingface import HuggingFaceService
    
    hf_service = HuggingFaceService()
    
    # Test COCO format annotations
    coco_annotations = [
        {
            "id": 1,
            "image_id": 123,
            "category_id": 62,  # chair in COCO
            "bbox": [100, 200, 50, 75],
            "area": 3750,
            "iscrowd": 0
        }
    ]
    
    is_coco = hf_service._is_coco_format(coco_annotations)
    assert is_coco, "Should detect COCO format"
    
    # Test non-COCO format
    standard_annotations = [
        {
            "category": "chair",
            "bbox": [100, 200, 50, 75],
            "confidence": 0.9
        }
    ]
    
    is_not_coco = hf_service._is_coco_format(standard_annotations)
    assert not is_not_coco, "Should not detect COCO format for standard annotations"
    
    print("✅ COCO format detection tests passed")


def test_coco_object_conversion():
    """Test COCO annotation conversion to Modomo format"""
    from app.services.huggingface import HuggingFaceService
    
    hf_service = HuggingFaceService()
    
    coco_annotations = [
        {
            "id": 1,
            "image_id": 123,
            "category_id": 62,  # chair in COCO
            "bbox": [100, 200, 50, 75],
            "area": 3750,
            "score": 0.95,
            "iscrowd": 0
        },
        {
            "id": 2,
            "image_id": 123,
            "category_id": 67,  # dining_table in COCO
            "bbox": [300, 400, 150, 100],
            "area": 15000,
            "score": 0.88,
            "iscrowd": 0
        }
    ]
    
    modomo_objects = hf_service._convert_coco_annotations_to_modomo(coco_annotations, "test-scene")
    
    assert len(modomo_objects) == 2, f"Expected 2 objects, got {len(modomo_objects)}"
    
    # Check first object (chair -> seating)
    chair_obj = modomo_objects[0]
    assert chair_obj["category"] == "seating", f"Expected 'seating', got '{chair_obj['category']}'"
    assert chair_obj["confidence"] == 0.95, f"Expected 0.95, got {chair_obj['confidence']}"
    assert chair_obj["bbox"] == [100, 200, 50, 75], f"Bbox mismatch: {chair_obj['bbox']}"
    
    # Check second object (dining_table -> tables)
    table_obj = modomo_objects[1]
    assert table_obj["category"] == "tables", f"Expected 'tables', got '{table_obj['category']}'"
    assert table_obj["confidence"] == 0.88, f"Expected 0.88, got {table_obj['confidence']}"
    
    print("✅ COCO object conversion tests passed")


def test_enhanced_metadata_processing():
    """Test enhanced metadata processing with skip_ai logic"""
    from app.services.huggingface import HuggingFaceService
    
    # Mock settings to control behavior
    with patch('app.services.huggingface.settings') as mock_settings:
        mock_settings.PREFER_EXISTING_ANNOTATIONS = True
        mock_settings.FORCE_AI_REPROCESSING = False
        mock_settings.MIN_SCENE_CONFIDENCE = 0.6
        mock_settings.MIN_OBJECT_CONFIDENCE = 0.5
        mock_settings.MIN_STYLE_CONFIDENCE = 0.5
        mock_settings.REQUIRE_BBOX_VALIDATION = True
        
        hf_service = HuggingFaceService()
        
        # Test metadata with high confidence
        high_conf_metadata = {
            "room_type": "living_room",
            "room_type_confidence": 0.85,
            "style": "contemporary",
            "style_confidence": 0.78,
            "annotations": [
                {
                    "category_id": 62,  # chair
                    "bbox": [100, 200, 50, 75],
                    "score": 0.92,
                    "id": 1,
                    "image_id": 123,
                    "area": 3750
                }
            ]
        }
        
        result = hf_service.handle_existing_hf_metadata(high_conf_metadata, "test-scene", 42)
        
        # Should skip scene classification and style analysis due to high confidence
        assert result["skip_ai"]["scene_classification"] == True, "Should skip scene classification"
        assert result["skip_ai"]["style_analysis"] == True, "Should skip style analysis"
        assert result["skip_ai"]["object_detection"] == True, "Should skip object detection"
        
        # Check scene updates
        assert result["scene_updates"]["scene_type"] == "living_room"
        assert result["scene_updates"]["scene_conf"] == 0.85
        assert result["scene_updates"]["primary_style"] == "contemporary"
        assert result["scene_updates"]["style_confidence"] == 0.78
        
        # Check objects were converted
        assert len(result["objects_data"]) == 1
        assert result["objects_data"][0]["category"] == "seating"
        
        print("✅ High confidence metadata processing tests passed")


def test_low_confidence_fallback():
    """Test that low confidence metadata falls back to AI processing"""
    from app.services.huggingface import HuggingFaceService
    
    with patch('app.services.huggingface.settings') as mock_settings:
        mock_settings.PREFER_EXISTING_ANNOTATIONS = True
        mock_settings.FORCE_AI_REPROCESSING = False
        mock_settings.MIN_SCENE_CONFIDENCE = 0.8  # High threshold
        mock_settings.MIN_OBJECT_CONFIDENCE = 0.8  # High threshold
        mock_settings.MIN_STYLE_CONFIDENCE = 0.8   # High threshold
        
        hf_service = HuggingFaceService()
        
        # Test metadata with low confidence
        low_conf_metadata = {
            "room_type": "living_room",
            "room_type_confidence": 0.5,  # Below threshold
            "style": "contemporary", 
            "style_confidence": 0.6,  # Below threshold
            "objects": [
                {
                    "category": "chair",
                    "bbox": [100, 200, 50, 75],
                    "confidence": 0.7  # Below threshold
                }
            ]
        }
        
        result = hf_service.handle_existing_hf_metadata(low_conf_metadata, "test-scene", 42)
        
        # Should NOT skip AI processing due to low confidence
        assert result["skip_ai"]["scene_classification"] == False, "Should NOT skip scene classification"
        assert result["skip_ai"]["style_analysis"] == False, "Should NOT skip style analysis"
        assert result["skip_ai"]["object_detection"] == False, "Should NOT skip object detection"
        
        # Should have no objects due to confidence filtering
        assert len(result["objects_data"]) == 0, "Should have no objects due to low confidence"
        
        print("✅ Low confidence fallback tests passed")


def test_force_reprocessing():
    """Test force reprocessing configuration"""
    from app.services.huggingface import HuggingFaceService
    
    with patch('app.services.huggingface.settings') as mock_settings:
        mock_settings.PREFER_EXISTING_ANNOTATIONS = True
        mock_settings.FORCE_AI_REPROCESSING = True  # Force reprocessing
        mock_settings.MIN_SCENE_CONFIDENCE = 0.6
        
        hf_service = HuggingFaceService()
        
        metadata = {
            "room_type": "living_room",
            "room_type_confidence": 0.95,  # High confidence
            "objects": [
                {
                    "category": "chair",
                    "bbox": [100, 200, 50, 75],
                    "confidence": 0.95
                }
            ]
        }
        
        result = hf_service.handle_existing_hf_metadata(metadata, "test-scene", 42)
        
        # Should NOT skip anything due to force reprocessing
        assert result["skip_ai"]["scene_classification"] == False, "Should NOT skip scene classification"
        assert result["skip_ai"]["object_detection"] == False, "Should NOT skip object detection"
        
        print("✅ Force reprocessing tests passed")


def run_all_tests():
    """Run all enhanced HuggingFace metadata tests"""
    print("Running enhanced HuggingFace metadata processing tests...\n")
    
    try:
        test_coco_format_detection()
        test_coco_object_conversion()
        test_enhanced_metadata_processing()
        test_low_confidence_fallback()
        test_force_reprocessing()
        
        print("\n🎉 All enhanced HuggingFace metadata tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)