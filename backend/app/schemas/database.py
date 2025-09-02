"""
Pydantic schemas matching the actual Supabase database structure
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

# Enums from database
JobKind = Literal["ingest", "process"]
JobStatus = Literal["queued", "running", "succeeded", "failed", "skipped"]
ReviewVerdict = Literal["approve", "reject", "edit"]
TargetType = Literal["scene", "object"]
ArtifactType = Literal["original", "depth", "mask", "thumb"]

# Lookup table schemas
class SceneLabel(BaseModel):
    """Scene type labels"""
    code: str
    display: str
    created_at: datetime

class StyleLabel(BaseModel):
    """Style labels"""
    code: str
    display: str
    created_at: datetime

class MaterialLabel(BaseModel):
    """Material labels"""
    code: str
    display: str
    created_at: datetime

class Category(BaseModel):
    """Furniture/object categories"""
    code: str
    display: str
    family: str
    parent_code: Optional[str] = None
    created_at: datetime

class CategoryAlias(BaseModel):
    """Category aliases/synonyms"""
    alias: str
    canonical: str
    kind: Optional[str] = None

# Dataset schemas
class Dataset(BaseModel):
    """Dataset from database"""
    id: UUID
    name: str
    version: Optional[str] = None
    source_url: Optional[str] = None
    license: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

class DatasetCreate(BaseModel):
    """Create dataset request"""
    name: str = Field(..., min_length=1, max_length=255)
    version: Optional[str] = None
    source_url: Optional[str] = None
    license: Optional[str] = None
    notes: Optional[str] = None

# Job schemas
class Job(BaseModel):
    """Job from database"""
    id: str
    kind: JobKind
    status: JobStatus
    dataset_id: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime

class JobCreate(BaseModel):
    """Create job request"""
    kind: JobKind
    dataset_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class JobEvent(BaseModel):
    """Job event from database"""
    id: str
    job_id: str
    name: str
    data: Optional[Dict[str, Any]] = None
    at: datetime

# Scene schemas
class Scene(BaseModel):
    """Scene from database"""
    id: UUID
    dataset_id: Optional[UUID] = None
    source: str
    r2_key_original: str
    width: Optional[int] = None
    height: Optional[int] = None
    phash: Optional[str] = None
    scene_type: Optional[str] = None  # FK to scene_labels.code
    scene_conf: Optional[float] = None
    palette: Optional[List[Dict[str, Any]]] = None  # [{"hex": "#aabbcc", "p": 0.23}]
    depth_key: Optional[str] = None
    status: str = "processed"
    created_at: datetime

class SceneCreate(BaseModel):
    """Create scene request"""
    dataset_id: Optional[UUID] = None
    source: str
    r2_key_original: str
    width: Optional[int] = None
    height: Optional[int] = None
    phash: Optional[str] = None

class SceneStyle(BaseModel):
    """Scene style relationship"""
    scene_id: UUID
    style_code: str
    conf: float

# Object schemas
class SceneObject(BaseModel):
    """Object from database"""
    id: UUID
    scene_id: UUID
    category_code: str  # FK to categories.code
    subcategory: Optional[str] = None
    bbox_x: float
    bbox_y: float
    bbox_w: float
    bbox_h: float
    confidence: float
    mask_key: Optional[str] = None
    thumb_key: Optional[str] = None
    depth_key: Optional[str] = None
    description: Optional[str] = None
    attrs: Optional[Dict[str, Any]] = None
    created_at: datetime

class ObjectMaterial(BaseModel):
    """Object material relationship"""
    object_id: UUID
    material_code: str
    conf: float

# Review schemas
class Review(BaseModel):
    """Review from database"""
    id: UUID
    target: TargetType
    target_id: UUID
    field: Optional[str] = None
    before_json: Optional[Dict[str, Any]] = None
    after_json: Optional[Dict[str, Any]] = None
    verdict: ReviewVerdict
    reviewer_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

class ReviewCreate(BaseModel):
    """Create review request"""
    target: TargetType
    target_id: UUID
    field: Optional[str] = None
    before_json: Optional[Dict[str, Any]] = None
    after_json: Optional[Dict[str, Any]] = None
    verdict: ReviewVerdict
    reviewer_id: Optional[str] = None
    notes: Optional[str] = None

# API Response schemas
class PaginatedResponse(BaseModel):
    """Paginated response"""
    data: List[Any]
    count: int
    page: int
    per_page: int
    total_pages: int

# Enhanced schemas with joined data
class SceneWithDetails(Scene):
    """Scene with related data"""
    dataset_name: Optional[str] = None
    scene_type_display: Optional[str] = None
    styles: List[SceneStyle] = []
    objects: List[SceneObject] = []

class ObjectWithDetails(SceneObject):
    """Object with related data"""
    category_display: Optional[str] = None
    category_family: Optional[str] = None
    materials: List[ObjectMaterial] = []