#!/usr/bin/env python3
"""
Simple test for HuggingFace URL validation (no HF dependencies needed)
"""

import re

def test_url_validation():
    """Test HuggingFace URL validation without imports"""
    HF_URL_PATTERN = re.compile(r'^https://huggingface\.co/datasets/([\w-]+)/([\w-]+)(?:/.*)?$')
    
    def validate_hf_url(url):
        match = HF_URL_PATTERN.match(url)
        return (match.group(1), match.group(2)) if match else None
    
    # Valid URLs
    result1 = validate_hf_url("https://huggingface.co/datasets/nlphuji/flickr30k")
    assert result1 == ("nlphuji", "flickr30k"), f"Expected ('nlphuji', 'flickr30k'), got {result1}"
    
    result2 = validate_hf_url("https://huggingface.co/datasets/username/dataset-name")
    assert result2 == ("username", "dataset-name"), f"Expected ('username', 'dataset-name'), got {result2}"
    
    # Invalid URLs
    assert validate_hf_url("https://example.com/dataset") is None
    assert validate_hf_url("invalid-url") is None
    assert validate_hf_url("") is None
    
    print("✅ URL validation tests passed")

if __name__ == "__main__":
    print("Running simple HuggingFace URL validation tests...")
    test_url_validation()
    print("\n🎉 All tests passed!")