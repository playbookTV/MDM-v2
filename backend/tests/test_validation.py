"""
Test cases for URL validation and security utilities
"""

import pytest
from fastapi import HTTPException
from app.core.validation import validate_url, validate_huggingface_url


class TestURLValidation:
    """Test URL validation functionality"""
    
    def test_valid_https_urls(self):
        """Test validation of valid HTTPS URLs"""
        # Valid HuggingFace URLs should pass
        valid_urls = [
            "https://huggingface.co/datasets/nlphuji/flickr30k",
            "https://huggingface.co/datasets/microsoft/coco",
            "https://hf.co/datasets/imagenet-1k"
        ]
        
        for url in valid_urls:
            assert validate_url(url, allowed_domains={'huggingface.co', 'hf.co'}) is True
    
    def test_invalid_schemes(self):
        """Test rejection of invalid URL schemes"""
        invalid_schemes = [
            "ftp://huggingface.co/datasets/test",
            "file:///etc/passwd",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>"
        ]
        
        for url in invalid_schemes:
            with pytest.raises(HTTPException) as exc_info:
                validate_url(url)
            assert exc_info.value.status_code == 400
            assert "scheme" in exc_info.value.detail.lower()
    
    def test_private_ip_blocking(self):
        """Test blocking of private IP addresses and localhost"""
        private_urls = [
            "https://localhost/datasets/test",
            "https://127.0.0.1/datasets/test", 
            "https://192.168.1.1/datasets/test",
            "https://10.0.0.1/datasets/test",
            "https://172.16.0.1/datasets/test",
            "https://169.254.1.1/datasets/test"
        ]
        
        for url in private_urls:
            with pytest.raises(HTTPException) as exc_info:
                validate_url(url)
            assert exc_info.value.status_code == 400
            assert "private" in exc_info.value.detail.lower() or "local" in exc_info.value.detail.lower()
    
    def test_domain_restrictions(self):
        """Test domain whitelist enforcement"""
        # Allowed domain should pass
        assert validate_url(
            "https://huggingface.co/datasets/test", 
            allowed_domains={'huggingface.co'}
        ) is True
        
        # Disallowed domain should fail
        with pytest.raises(HTTPException) as exc_info:
            validate_url(
                "https://evil.com/datasets/test", 
                allowed_domains={'huggingface.co'}
            )
        assert exc_info.value.status_code == 400
        assert "not allowed" in exc_info.value.detail.lower()
    
    def test_url_length_validation(self):
        """Test URL length limits"""
        # Very long URL should be rejected
        long_url = "https://huggingface.co/" + "x" * 2500
        
        with pytest.raises(HTTPException) as exc_info:
            validate_url(long_url)
        assert exc_info.value.status_code == 400
        assert "too long" in exc_info.value.detail.lower()
    
    def test_malformed_urls(self):
        """Test rejection of malformed URLs"""
        malformed_urls = [
            "",
            "not-a-url",
            "://missing-scheme.com",
            "https://", 
            "https:///no-host",
            None
        ]
        
        for url in malformed_urls:
            with pytest.raises(HTTPException) as exc_info:
                if url is None:
                    validate_url(url)
                else:
                    validate_url(url)
            assert exc_info.value.status_code == 400


class TestHuggingFaceURLValidation:
    """Test HuggingFace specific URL validation"""
    
    def test_valid_huggingface_urls(self):
        """Test validation of valid HuggingFace dataset URLs"""
        valid_urls = [
            "https://huggingface.co/datasets/nlphuji/flickr30k",
            "https://huggingface.co/datasets/microsoft/coco",
            "https://huggingface.co/datasets/org/dataset-name",
            "https://hf.co/datasets/simple-name"
        ]
        
        for url in valid_urls:
            assert validate_huggingface_url(url) is True
    
    def test_non_dataset_huggingface_urls(self):
        """Test rejection of non-dataset HuggingFace URLs"""
        non_dataset_urls = [
            "https://huggingface.co/models/bert-base-uncased",
            "https://huggingface.co/spaces/gradio/hello_world", 
            "https://huggingface.co/docs/transformers",
            "https://huggingface.co/",
            "https://huggingface.co/datasets/"  # Missing dataset name
        ]
        
        for url in non_dataset_urls:
            with pytest.raises(HTTPException) as exc_info:
                validate_huggingface_url(url)
            assert exc_info.value.status_code == 400
            assert "dataset" in exc_info.value.detail.lower()
    
    def test_invalid_huggingface_domains(self):
        """Test rejection of non-HuggingFace domains"""
        invalid_domains = [
            "https://github.com/datasets/test",
            "https://kaggle.com/datasets/test",
            "https://evil-huggingface.co/datasets/test"
        ]
        
        for url in invalid_domains:
            with pytest.raises(HTTPException) as exc_info:
                validate_huggingface_url(url)
            assert exc_info.value.status_code == 400
            assert "allowed" in exc_info.value.detail.lower()
    
    def test_huggingface_dataset_name_validation(self):
        """Test dataset name validation in URLs"""
        # Valid dataset names
        valid_names = [
            "https://huggingface.co/datasets/simple",
            "https://huggingface.co/datasets/org/name",
            "https://huggingface.co/datasets/org/sub/name"
        ]
        
        for url in valid_names:
            assert validate_huggingface_url(url) is True
        
        # Invalid dataset names (too long)
        long_name = "x" * 250
        with pytest.raises(HTTPException) as exc_info:
            validate_huggingface_url(f"https://huggingface.co/datasets/{long_name}")
        assert exc_info.value.status_code == 400