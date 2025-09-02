"""
Authentication utilities
"""

from typing import Optional
from fastapi import Request


def get_current_user(request: Request = None) -> str:
    """
    Get the current authenticated user.
    
    For now, returns 'system' as a placeholder until proper auth is implemented.
    In the future, this should extract user info from JWT tokens or session data.
    """
    # TODO: Implement proper authentication
    # This would typically:
    # 1. Extract JWT token from Authorization header
    # 2. Validate token and extract user info
    # 3. Return user ID or username
    
    return "system"


def get_current_user_id(request: Request = None) -> Optional[str]:
    """Get current user ID from authentication context"""
    return get_current_user(request)