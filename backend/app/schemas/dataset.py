"""
Dataset-related Pydantic schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .common import BboxModel, StyleClassification

# Dataset schemas
class DatasetBase(BaseModel):
    """Base dataset fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")
    tags: List[str] = Field(default_factory=list, description="Dataset tags")

class DatasetCreate(DatasetBase):
    """Create dataset request"""
    source: str = Field(..., description="Dataset source: upload, huggingface, url")
    source_url: Optional[str] = Field(None, description="Source URL if applicable")

class Dataset(DatasetBase):
    """Dataset response model"""
    id: str = Field(..., description="Dataset ID")
    source: str = Field(..., description="Dataset source")
    source_url: Optional[str] = Field(None, description="Source URL")
    total_scenes: int = Field(..., description="Total number of scenes")
    processed_scenes: int = Field(..., description="Number of processed scenes")
    total_objects: int = Field(..., description="Total number of detected objects")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True

# Scene schemas
class SceneObjectBase(BaseModel):
    """Base scene object fields"""
    label: str = Field(..., description="Object label")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    bbox: BboxModel = Field(..., description="Bounding box")
    category: Optional[str] = Field(None, description="Object category")
    material: Optional[str] = Field(None, description="Material classification")
    material_conf: Optional[float] = Field(None, ge=0, le=1, description="Material confidence")
    description: Optional[str] = Field(None, description="Object description")

class SceneObject(SceneObjectBase):
    """Scene object response model"""
    id: str = Field(..., description="Object ID")
    scene_id: str = Field(..., description="Scene ID")
    r2_key_mask: Optional[str] = Field(None, description="R2 key for segmentation mask")
    r2_key_thumbnail: Optional[str] = Field(None, description="R2 key for thumbnail")
    review_status: Optional[str] = Field(None, description="Review status")
    review_notes: Optional[str] = Field(None, description="Review notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True

class SceneBase(BaseModel):
    """Base scene fields"""
    source: str = Field(..., description="Original filename")
    width: int = Field(..., gt=0, description="Image width")
    height: int = Field(..., gt=0, description="Image height")

class SceneCreate(SceneBase):
    """Create scene request"""
    r2_key_original: str = Field(..., description="R2 key for original image")
    attrs: Optional[Dict[str, Any]] = Field(None, description="Additional attributes")

class Scene(SceneBase):
    """Scene response model"""
    id: str = Field(..., description="Scene ID")
    dataset_id: str = Field(..., description="Dataset ID")
    dataset_name: Optional[str] = Field(None, description="Dataset name")
    r2_key_original: str = Field(..., description="R2 key for original image")
    r2_key_thumbnail: Optional[str] = Field(None, description="R2 key for thumbnail")
    r2_key_depth: Optional[str] = Field(None, description="R2 key for depth map")
    
    # Classification results
    scene_type: Optional[str] = Field(None, description="Scene type classification")
    scene_conf: Optional[float] = Field(None, ge=0, le=1, description="Scene classification confidence")
    styles: List[StyleClassification] = Field(default_factory=list, description="Style classifications")
    palette: List[str] = Field(default_factory=list, description="Color palette (hex colors)")
    
    # Status
    status: str = Field(..., description="Processing status")
    processing_error: Optional[str] = Field(None, description="Processing error message")
    review_status: Optional[str] = Field(None, description="Review status")
    review_notes: Optional[str] = Field(None, description="Review notes")
    reviewed_by: Optional[str] = Field(None, description="Reviewer name")
    reviewed_at: Optional[datetime] = Field(None, description="Review timestamp")
    
    # Objects (optional, loaded on demand)
    objects: Optional[List[SceneObject]] = Field(None, description="Detected objects")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")

    class Config:
        from_attributes = True

# Upload-related schemas
class PresignFileRequest(BaseModel):
    """Single file presign request"""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="File MIME type")

class PresignRequest(BaseModel):
    """Presigned URLs request"""
    files: List[PresignFileRequest] = Field(..., description="Files to upload")

class PresignUpload(BaseModel):
    """Single presigned upload response"""
    filename: str = Field(..., description="Original filename")
    key: str = Field(..., description="R2 object key")
    url: str = Field(..., description="Presigned upload URL")
    headers: Dict[str, str] = Field(..., description="Required headers")

class PresignResponse(BaseModel):
    """Presigned URLs response"""
    uploads: List[PresignUpload] = Field(..., description="Upload information")

class RegisterScenesRequest(BaseModel):
    """Register scenes request"""
    scenes: List[SceneCreate] = Field(..., description="Scenes to register")

class RegisterScenesResponse(BaseModel):
    """Register scenes response"""
    created: int = Field(..., description="Number of scenes created")
    scene_ids: List[str] = Field(..., description="Created scene IDs")