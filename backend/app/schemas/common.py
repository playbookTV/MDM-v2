"""
Common Pydantic schemas and base models
"""

from typing import Generic, List, Optional, TypeVar, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')

class APIError(BaseModel):
    """Standard API error response"""
    error: Dict[str, Any] = Field(..., description="Error details")

class Page(BaseModel, Generic[T]):
    """Paginated response model"""
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number (1-indexed)")
    limit: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")

class BboxModel(BaseModel):
    """Bounding box model"""
    x: float = Field(..., ge=0, description="X coordinate")
    y: float = Field(..., ge=0, description="Y coordinate") 
    width: float = Field(..., gt=0, description="Width")
    height: float = Field(..., gt=0, description="Height")

class StyleClassification(BaseModel):
    """Style classification result"""
    code: str = Field(..., description="Style code")
    conf: float = Field(..., ge=0, le=1, description="Confidence score")