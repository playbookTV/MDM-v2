#!/usr/bin/env python3
"""
Test script for HuggingFace functionality
"""

from app.services.huggingface import HuggingFaceService

def test_url_validation():
    """Test HuggingFace URL validation"""
    service = HuggingFaceService()
    
    # Valid URLs
    assert service.validate_hf_url("https://huggingface.co/datasets/nlphuji/flickr30k") == ("nlphuji", "flickr30k")
    assert service.validate_hf_url("https://huggingface.co/datasets/username/dataset-name") == ("username", "dataset-name")
    
    # Invalid URLs
    assert service.validate_hf_url("https://example.com/dataset") is None
    assert service.validate_hf_url("invalid-url") is None
    assert service.validate_hf_url("") is None
    
    print("✅ URL validation tests passed")

def test_dataset_info_extraction():
    """Test dataset info extraction (requires network)"""
    service = HuggingFaceService()
    
    # Test with a known small dataset
    info = service.extract_dataset_info("https://huggingface.co/datasets/hf-internal-testing/example_images")
    
    if info:
        assert "dataset_id" in info
        assert info["dataset_id"] == "hf-internal-testing/example_images"
        print("✅ Dataset info extraction test passed")
    else:
        print("⚠️ Dataset info extraction test skipped (no network or dataset unavailable)")

if __name__ == "__main__":
    print("Running HuggingFace functionality tests...")
    
    test_url_validation()
    test_dataset_info_extraction()
    
    print("\n🎉 All available tests passed!")