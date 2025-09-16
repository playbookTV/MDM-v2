#!/usr/bin/env python3
"""
Test script for Roboflow integration
"""

import os
import sys
import logging
from unittest.mock import Mock

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_roboflow_service():
    """Test basic RoboflowService functionality"""
    print("🧪 Testing Roboflow Service Integration")
    print("=" * 50)
    
    try:
        from app.services.roboflow import RoboflowService
        
        # Test 1: Create RoboflowService instance
        print("✅ Test 1: Creating RoboflowService instance")
        service = RoboflowService()
        assert service is not None, "Service should be created"
        print("   ✓ RoboflowService created successfully")
        
        # Test 2: URL validation
        print("\n✅ Test 2: URL validation")
        
        # Valid URLs
        valid_url = "https://universe.roboflow.com/roboflow-100/furniture-ngpea/model/1"
        result = service.validate_roboflow_url(valid_url)
        assert result is not None, "Valid URL should pass validation"
        assert result[0] == "roboflow-100", f"Expected workspace 'roboflow-100', got '{result[0]}'"
        assert result[1] == "furniture-ngpea", f"Expected project 'furniture-ngpea', got '{result[1]}'"
        assert result[2] == "1", f"Expected version '1', got '{result[2]}'"
        print(f"   ✓ Valid URL parsed correctly: {result}")
        
        # Invalid URLs
        invalid_urls = [
            "https://invalid-url.com",
            "https://universe.roboflow.com/invalid",
            "not-a-url",
            ""
        ]
        
        for invalid_url in invalid_urls:
            result = service.validate_roboflow_url(invalid_url)
            assert result is None, f"Invalid URL should fail validation: {invalid_url}"
        print("   ✓ Invalid URLs rejected correctly")
        
        # Test 3: Dataset info extraction (without API key - should handle gracefully)
        print("\n✅ Test 3: Dataset info extraction")
        info = service.extract_dataset_info(valid_url, "fake_api_key")
        # Should return empty dict due to invalid API key, but not crash
        assert isinstance(info, dict), "Should return a dictionary"
        print("   ✓ Dataset info extraction handles invalid API key gracefully")
        
        # Test 4: Annotation conversion
        print("\n✅ Test 4: Annotation conversion")
        sample_metadata = {
            "image_id": 1,
            "annotations": [
                {
                    "bbox": [100, 200, 50, 80],
                    "category": "chair",
                    "confidence": 0.95,
                    "area": 4000,
                    "id": 1
                }
            ]
        }
        
        conversion_result = service.handle_existing_roboflow_metadata(
            sample_metadata, "test_scene_123", 0
        )
        
        assert isinstance(conversion_result, dict), "Should return a dictionary"
        assert "scene_updates" in conversion_result, "Should have scene_updates key"
        assert "objects_data" in conversion_result, "Should have objects_data key"
        assert "skip_ai" in conversion_result, "Should have skip_ai key"
        
        print(f"   ✓ Metadata conversion successful")
        print(f"   ℹ️  Objects found: {len(conversion_result['objects_data'])}")
        
        if conversion_result['objects_data']:
            obj = conversion_result['objects_data'][0]
            print(f"   ℹ️  Sample object: {obj['category']} (confidence: {obj['confidence']})")
            assert obj['bbox'] == [100, 200, 50, 80], "BBox should be preserved"
            
        print("\n🎉 All Roboflow service tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_roboflow_api_imports():
    """Test that all required imports work"""
    print("\n🧪 Testing Roboflow API Imports")
    print("=" * 50)
    
    try:
        # Test importing roboflow package
        try:
            import roboflow
            from roboflow import Roboflow
            print("✅ Roboflow SDK imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import Roboflow SDK: {e}")
            return False
        
        # Test our service imports
        from app.services.roboflow import RoboflowService
        from app.worker.roboflow_tasks import process_roboflow_dataset, validate_roboflow_url
        
        print("✅ All Roboflow integration imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_schemas():
    """Test Roboflow API schemas"""
    print("\n🧪 Testing Roboflow API Schemas")
    print("=" * 50)
    
    try:
        # Test importing the request/response schemas
        from app.api.routes.datasets_new import ProcessRoboflowRequest, ProcessRoboflowResponse
        
        # Test creating a request schema
        test_request = ProcessRoboflowRequest(
            roboflow_url="https://universe.roboflow.com/roboflow-100/furniture-ngpea/model/1",
            api_key="test_key",
            export_format="coco",
            max_images=10
        )
        
        assert test_request.roboflow_url.startswith("https://universe.roboflow.com")
        assert test_request.api_key == "test_key"
        assert test_request.export_format == "coco"
        assert test_request.max_images == 10
        
        print("✅ Request schema works correctly")
        
        # Test response schema
        test_response = ProcessRoboflowResponse(
            job_id="test-job-123",
            status="started"
        )
        
        assert test_response.job_id == "test-job-123"
        assert test_response.status == "started"
        
        print("✅ Response schema works correctly")
        print("🎉 All schema tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Roboflow Integration Tests")
    print("=" * 60)
    
    # Mock any dependencies that might not be available in test environment
    from unittest.mock import patch
    
    with patch('app.services.roboflow.StorageService'), \
         patch('app.services.roboflow.DatasetService'):
        
        tests = [
            ("API Imports", test_roboflow_api_imports),
            ("Service Functionality", test_roboflow_service),
            ("API Schemas", test_schemas),
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
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed! Roboflow integration is ready!")
            return True
        else:
            print("❌ Some tests failed. Please check the integration.")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)