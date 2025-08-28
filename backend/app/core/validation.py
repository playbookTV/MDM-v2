"""
URL validation and security utilities
"""

import re
import logging
from urllib.parse import urlparse
from typing import Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Allowed domains for external URLs
ALLOWED_DOMAINS = {
    'huggingface.co',
    'hf.co'
}

# Blocked domains and patterns
BLOCKED_DOMAINS = {
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '::1',
    'local',
}

# Private IP ranges (CIDR notation)
PRIVATE_IP_PATTERNS = [
    r'^127\.',          # 127.0.0.0/8
    r'^10\.',           # 10.0.0.0/8
    r'^172\.(1[6-9]|2\d|3[01])\.',  # 172.16.0.0/12
    r'^192\.168\.',     # 192.168.0.0/16
    r'^169\.254\.',     # 169.254.0.0/16 (link-local)
    r'^::1$',           # IPv6 loopback
    r'^fc00:',          # IPv6 private
    r'^fe80:',          # IPv6 link-local
]

def validate_url(url: str, allowed_schemes: Optional[set] = None, allowed_domains: Optional[set] = None) -> bool:
    """
    Validate URL for security and format.
    
    Args:
        url: URL to validate
        allowed_schemes: Set of allowed schemes (default: https, http)
        allowed_domains: Set of allowed domains (default: ALLOWED_DOMAINS)
        
    Returns:
        True if URL is valid and safe
        
    Raises:
        HTTPException: If URL is invalid or unsafe
    """
    if not url or not isinstance(url, str):
        raise HTTPException(status_code=400, detail="URL is required and must be a string")
    
    if allowed_schemes is None:
        allowed_schemes = {'http', 'https'}
        
    if allowed_domains is None:
        allowed_domains = ALLOWED_DOMAINS
    
    try:
        parsed = urlparse(url.lower().strip())
        
        # Check scheme
        if parsed.scheme not in allowed_schemes:
            raise HTTPException(
                status_code=400,
                detail=f"URL scheme must be one of: {', '.join(allowed_schemes)}"
            )
        
        # Check if hostname exists
        if not parsed.hostname:
            raise HTTPException(status_code=400, detail="URL must have a valid hostname")
        
        hostname = parsed.hostname.lower()
        
        # Check against blocked domains
        if hostname in BLOCKED_DOMAINS:
            raise HTTPException(
                status_code=400,
                detail="Access to local/private resources is not allowed"
            )
        
        # Check for private IP ranges
        for pattern in PRIVATE_IP_PATTERNS:
            if re.match(pattern, hostname):
                raise HTTPException(
                    status_code=400,
                    detail="Access to private IP ranges is not allowed"
                )
        
        # Check if domain is in allowed list
        if allowed_domains and hostname not in allowed_domains:
            # Check for subdomains
            domain_parts = hostname.split('.')
            if len(domain_parts) >= 2:
                parent_domain = '.'.join(domain_parts[-2:])
                if parent_domain not in allowed_domains:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Domain not allowed. Allowed domains: {', '.join(allowed_domains)}"
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Domain not allowed. Allowed domains: {', '.join(allowed_domains)}"
                )
        
        # Additional URL length check
        if len(url) > 2048:
            raise HTTPException(status_code=400, detail="URL is too long (max 2048 characters)")
        
        logger.info(f"URL validation passed: {hostname}")
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL validation error for {url}: {e}")
        raise HTTPException(status_code=400, detail="Invalid URL format")

def validate_huggingface_url(url: str) -> bool:
    """
    Specifically validate HuggingFace dataset URLs.
    
    Args:
        url: HuggingFace URL to validate
        
    Returns:
        True if valid HuggingFace dataset URL
        
    Raises:
        HTTPException: If URL is invalid
    """
    # First run general URL validation
    validate_url(url, allowed_domains={'huggingface.co', 'hf.co'})
    
    try:
        parsed = urlparse(url.lower().strip())
        path = parsed.path
        
        # Check if it's a dataset URL (not model, space, etc.)
        if not path.startswith('/datasets/'):
            raise HTTPException(
                status_code=400,
                detail="URL must be a HuggingFace dataset URL (https://huggingface.co/datasets/...)"
            )
        
        # Extract dataset name from path
        path_parts = path.strip('/').split('/')
        if len(path_parts) < 2 or path_parts[0] != 'datasets':
            raise HTTPException(
                status_code=400,
                detail="Invalid HuggingFace dataset URL format"
            )
        
        dataset_name = '/'.join(path_parts[1:])  # Everything after /datasets/
        
        # Basic dataset name validation
        if not dataset_name or len(dataset_name) > 200:
            raise HTTPException(
                status_code=400,
                detail="Invalid dataset name in URL"
            )
        
        logger.info(f"HuggingFace URL validation passed: {dataset_name}")
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HuggingFace URL validation error for {url}: {e}")
        raise HTTPException(status_code=400, detail="Invalid HuggingFace dataset URL")