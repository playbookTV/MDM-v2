"""
Test HuggingFace metadata handling functionality
"""

import pytest
from unittest.mock import Mock, patch
from app.services.huggingface import HuggingFaceService


class TestHFMetadataHandling:
    """Test metadata processing for HuggingFace datasets"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.hf_service = HuggingFaceService()
        self.test_scene_id = "test-scene-123"
        self.test_hf_index = 42
    
    def test_empty_metadata_returns_safe_defaults(self):
        """Test that empty/invalid metadata returns safe defaults without errors"""
        # Test empty metadata
        result = self.hf_service.handle_existing_hf_metadata({}, self.test_scene_id, self.test_hf_index)
        
        assert result["scene_updates"] == {}
        assert result["objects_data"] == []
        assert all(not skip for skip in result["skip_ai"].values())
        
        # Test None metadata
        result = self.hf_service.handle_existing_hf_metadata(None, self.test_scene_id, self.test_hf_index)
        
        assert result["scene_updates"] == {}
        assert result["objects_data"] == []
        assert all(not skip for skip in result["skip_ai"].values())
    
    def test_room_type_mapping_and_skip_ai(self):
        """Test HF room_type maps to scene_type and triggers skip_ai"""
        metadata = {
            "room_type": "living_room",
            "room_type_confidence": 0.85,
            "other_field": "preserved"
        }
        
        result = self.hf_service.handle_existing_hf_metadata(metadata, self.test_scene_id, self.test_hf_index)
        
        # Check scene type mapping
        assert result["scene_updates"]["scene_type"] == "living_room"
        assert result["scene_updates"]["scene_conf"] == 0.85
        
        # Check skip_ai flag
        assert result["skip_ai"]["scene_classification"] is True
        assert result["skip_ai"]["object_detection"] is False  # Should still be False
        
        # Check original metadata preserved
        assert result["scene_updates"]["attrs"]["room_type"] == "living_room"
        assert result["scene_updates"]["attrs"]["other_field"] == "preserved"
        assert result["scene_updates"]["attrs"]["hf_original_index"] == self.test_hf_index
    
    def test_object_detection_with_existing_objects(self):
        """Test that existing HF objects are converted and trigger skip_ai"""
        metadata = {
            "objects": [
                {
                    "category": "sofa",
                    "bbox": [100, 200, 300, 400],
                    "confidence": 0.9,
                    "description": "Large sectional sofa"
                },
                {
                    "label": "table",  # Different key name
                    "bounding_box": {"x": 50, "y": 60, "width": 120, "height": 80},  # Dict format
                    "score": 0.75  # Different key name
                }
            ]
        }
        
        result = self.hf_service.handle_existing_hf_metadata(metadata, self.test_scene_id, self.test_hf_index)
        
        # Check objects were converted
        assert len(result["objects_data"]) == 2
        
        # Check first object
        obj1 = result["objects_data"][0]
        assert obj1["category"] == "sofa"
        assert obj1["bbox"] == [100, 200, 300, 400]
        assert obj1["confidence"] == 0.9
        assert obj1["description"] == "Large sectional sofa"
        
        # Check second object with different format
        obj2 = result["objects_data"][1]
        assert obj2["category"] == "table"
        assert obj2["bbox"] == [50, 60, 120, 80]
        assert obj2["confidence"] == 0.75
        
        # Check skip_ai flag
        assert result["skip_ai"]["object_detection"] is True
    
    def test_caption_and_description_mapping(self):
        """Test that HF captions/descriptions are preserved"""
        metadata = {
            "caption": "A modern living room with contemporary furniture",
            "room_type": "living_room"
        }
        
        result = self.hf_service.handle_existing_hf_metadata(metadata, self.test_scene_id, self.test_hf_index)
        
        # Check description mapping
        assert result["scene_updates"]["description"] == "A modern living room with contemporary furniture"
        
        # Check both preserved in attrs
        assert result["scene_updates"]["attrs"]["caption"] == "A modern living room with contemporary furniture"
        assert result["scene_updates"]["attrs"]["room_type"] == "living_room"
    
    def test_style_and_color_analysis_mapping(self):
        """Test style and color analysis mapping from HF metadata"""
        metadata = {
            "style": "contemporary",
            "style_confidence": 0.82,
            "color_palette": ["#FFFFFF", "#000000", "#808080"],
            "dominant_colors": [
                {"color": "#FFFFFF", "percentage": 0.4},
                {"color": "#000000", "percentage": 0.3}
            ]
        }
        
        result = self.hf_service.handle_existing_hf_metadata(metadata, self.test_scene_id, self.test_hf_index)
        
        # Check style mapping
        assert result["scene_updates"]["primary_style"] == "contemporary"
        assert result["scene_updates"]["style_confidence"] == 0.82
        assert result["skip_ai"]["style_analysis"] is True
        
        # Check color analysis mapping (should use first matching key)
        assert result["scene_updates"]["color_analysis"] == ["#FFFFFF", "#000000", "#808080"]
        assert result["skip_ai"]["color_analysis"] is True
    
    def test_depth_map_detection(self):
        """Test depth map detection and skip_ai flag"""
        metadata = {
            "depth_map": "base64encodeddata...",
            "room_type": "bedroom"
        }
        
        result = self.hf_service.handle_existing_hf_metadata(metadata, self.test_scene_id, self.test_hf_index)
        
        # Check depth detection
        assert result["scene_updates"]["depth_available"] is True
        assert result["skip_ai"]["depth_estimation"] is True
    
    def test_material_detection(self):
        """Test material detection from HF metadata"""
        metadata = {
            "materials": ["wood", "fabric", "metal"],
            "room_type": "office"
        }
        
        result = self.hf_service.handle_existing_hf_metadata(metadata, self.test_scene_id, self.test_hf_index)
        
        # Check material detection
        assert result["skip_ai"]["material_classification"] is True
        
        # Test single material field
        metadata_single = {
            "material": "leather"
        }
        
        result_single = self.hf_service.handle_existing_hf_metadata(metadata_single, self.test_scene_id, self.test_hf_index)
        assert result_single["skip_ai"]["material_classification"] is True
    
    def test_object_bbox_format_conversion(self):
        """Test different bbox format conversions"""
        # Test [x1, y1, x2, y2] format
        hf_obj_xyxy = {
            "category": "chair",
            "bbox": [10, 20, 110, 120],  # x1,y1,x2,y2
            "confidence": 0.8,
            "x1": 10  # Indicator of xyxy format
        }
        
        converted = self.hf_service._convert_hf_object_to_modomo(hf_obj_xyxy, 0)
        assert converted["bbox"] == [10, 20, 100, 100]  # Converted to x,y,w,h
        
        # Test dict format
        hf_obj_dict = {
            "label": "table",
            "bounding_box": {"x": 50, "y": 60, "width": 100, "height": 80},
            "score": 0.7
        }
        
        converted = self.hf_service._convert_hf_object_to_modomo(hf_obj_dict, 1)
        assert converted["category"] == "table"
        assert converted["bbox"] == [50, 60, 100, 80]
        assert converted["confidence"] == 0.7
    
    def test_object_bbox_invalid_format(self):
        """Test handling of invalid bbox formats"""
        hf_obj_invalid = {
            "category": "sofa",
            "confidence": 0.8
            # No bbox - should return None
        }
        
        converted = self.hf_service._convert_hf_object_to_modomo(hf_obj_invalid, 0)
        assert converted is None
    
    def test_comprehensive_metadata_processing(self):
        """Test comprehensive metadata with multiple components"""
        comprehensive_metadata = {
            "room_type": "living_room",
            "room_type_confidence": 0.95,
            "caption": "Modern living room with sectional sofa",
            "style": "contemporary", 
            "style_confidence": 0.88,
            "color_palette": ["#FFFFFF", "#808080", "#000000"],
            "depth_map": "exists",
            "materials": ["fabric", "wood", "metal"],
            "objects": [
                {
                    "category": "sofa",
                    "bbox": [100, 150, 400, 250],
                    "confidence": 0.92
                }
            ],
            "extra_field": "should_be_preserved"
        }
        
        result = self.hf_service.handle_existing_hf_metadata(
            comprehensive_metadata, self.test_scene_id, self.test_hf_index
        )
        
        # Check all components processed correctly
        assert result["scene_updates"]["scene_type"] == "living_room"
        assert result["scene_updates"]["scene_conf"] == 0.95
        assert result["scene_updates"]["description"] == "Modern living room with sectional sofa"
        assert result["scene_updates"]["primary_style"] == "contemporary"
        assert result["scene_updates"]["style_confidence"] == 0.88
        assert result["scene_updates"]["color_analysis"] == ["#FFFFFF", "#808080", "#000000"]
        assert result["scene_updates"]["depth_available"] is True
        
        # Check skip_ai flags
        assert result["skip_ai"]["scene_classification"] is True
        assert result["skip_ai"]["style_analysis"] is True
        assert result["skip_ai"]["color_analysis"] is True
        assert result["skip_ai"]["depth_estimation"] is True
        assert result["skip_ai"]["material_classification"] is True
        assert result["skip_ai"]["object_detection"] is True
        
        # Check objects
        assert len(result["objects_data"]) == 1
        assert result["objects_data"][0]["category"] == "sofa"
        
        # Check original metadata preserved
        assert result["scene_updates"]["attrs"]["extra_field"] == "should_be_preserved"
        assert result["scene_updates"]["attrs"]["hf_original_index"] == self.test_hf_index
    
    @patch('app.services.huggingface.logger')
    def test_error_handling_graceful_degradation(self, mock_logger):
        """Test that errors are handled gracefully without crashing"""
        # Simulate malformed metadata that causes exception
        malformed_metadata = {
            "objects": "not_a_list",  # Should cause error in object processing
            "room_type": None,  # Should cause error in string processing
            "style": {"nested": "dict"}  # Should cause error in string conversion
        }
        
        result = self.hf_service.handle_existing_hf_metadata(
            malformed_metadata, self.test_scene_id, self.test_hf_index
        )
        
        # Should return safe defaults with original metadata preserved
        assert "attrs" in result["scene_updates"]
        assert result["scene_updates"]["attrs"]["objects"] == "not_a_list"
        assert result["objects_data"] == []
        
        # Should have logged warning
        mock_logger.warning.assert_called()