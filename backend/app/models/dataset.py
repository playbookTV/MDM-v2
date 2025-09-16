"""
Database models for datasets and related entities
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, DateTime, Integer, Float, Boolean, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

class Dataset(Base):
    """Dataset model"""
    __tablename__ = "datasets"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # 'upload', 'huggingface', 'roboflow', 'url'
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Stats
    total_scenes: Mapped[int] = mapped_column(Integer, default=0)
    processed_scenes: Mapped[int] = mapped_column(Integer, default=0)
    total_objects: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    attrs: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    scenes: Mapped[List["Scene"]] = relationship("Scene", back_populates="dataset", cascade="all, delete-orphan")
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="dataset")


class Scene(Base):
    """Scene model"""
    __tablename__ = "scenes"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    
    # Source info
    source: Mapped[str] = mapped_column(String(255), nullable=False)  # original filename
    r2_key_original: Mapped[str] = mapped_column(String(500), nullable=False)
    r2_key_thumbnail: Mapped[Optional[str]] = mapped_column(String(500))
    depth_key: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Image dimensions
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Scene classification
    scene_type: Mapped[Optional[str]] = mapped_column(String(50))
    scene_conf: Mapped[Optional[float]] = mapped_column(Float)
    
    # Processing status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, processing, completed, failed
    processing_error: Mapped[Optional[str]] = mapped_column(Text)
    
    # Review status
    review_status: Mapped[Optional[str]] = mapped_column(String(20))  # pending, approved, rejected, corrected
    review_notes: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Style and color data
    styles: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)  # [{code, conf}, ...]
    palette: Mapped[List[str]] = mapped_column(JSON, default=list)  # hex colors
    
    # Metadata
    attrs: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    phash: Mapped[Optional[str]] = mapped_column(String(16))  # perceptual hash for deduplication
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="scenes")
    objects: Mapped[List["SceneObject"]] = relationship("SceneObject", back_populates="scene", cascade="all, delete-orphan")


class SceneObject(Base):
    """Detected object in a scene"""
    __tablename__ = "objects"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    
    # Object classification
    category_code: Mapped[str] = mapped_column(String(100), nullable=False)  # canonical category code
    subcategory: Mapped[Optional[str]] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Bounding box (stored as separate columns for fast querying)
    bbox_x: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_y: Mapped[float] = mapped_column(Float, nullable=False) 
    bbox_w: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_h: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Segmentation and visual features  
    mask_key: Mapped[Optional[str]] = mapped_column(String(500))
    thumb_key: Mapped[Optional[str]] = mapped_column(String(500))
    depth_key: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Review status
    review_status: Mapped[Optional[str]] = mapped_column(String(20))  # pending, approved, rejected, corrected
    review_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    attrs: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    scene: Mapped["Scene"] = relationship("Scene", back_populates="objects")


class Job(Base):
    """Processing job model"""
    __tablename__ = "jobs"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    
    # Job info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # 'process_scenes', 'extract_objects', etc.
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued, running, completed, failed, cancelled
    
    # Progress tracking
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    completed_items: Mapped[int] = mapped_column(Integer, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, default=0)
    
    # Configuration and results
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    result: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="jobs")


class SceneStyle(Base):
    """Scene to style relationship with confidence"""
    __tablename__ = "scene_styles"
    
    scene_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("scenes.id", ondelete="CASCADE"), primary_key=True)
    style_code: Mapped[str] = mapped_column(String(50), primary_key=True)  # references style_labels.code
    conf: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ObjectMaterial(Base):
    """Object to material relationship with confidence"""
    __tablename__ = "object_materials"
    
    object_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("objects.id", ondelete="CASCADE"), primary_key=True)
    material_code: Mapped[str] = mapped_column(String(50), primary_key=True)  # references material_labels.code
    conf: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())


class Review(Base):
    """Review/annotation model for tracking human corrections"""
    __tablename__ = "reviews"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))  # nullable for object-only reviews
    object_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))  # nullable for scene-only reviews
    
    # Review details
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # 'approve', 'reject', 'correct'
    changes: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)  # what was changed
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Session tracking
    session_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))
    reviewer: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())