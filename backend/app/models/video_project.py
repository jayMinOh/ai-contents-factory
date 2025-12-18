"""
Video Project ORM model for the AI Video Marketing Platform.

Represents a video project entity that links brand, product, and reference analysis
for AI-powered video generation workflow.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.product import Product
    from app.models.reference_analysis import ReferenceAnalysis
    from app.models.scene_image import SceneImage
    from app.models.scene_video import SceneVideo
    from app.models.storyboard import Storyboard


class VideoProject(Base, TimestampMixin):
    """
    Video Project model representing a video generation workflow.

    Attributes:
        id: UUID string primary key
        title: Project title
        description: Project description
        brand_id: Foreign key to Brand
        product_id: Foreign key to Product
        reference_analysis_id: Foreign key to ReferenceAnalysis
        status: Project status (draft, script_generating, etc.)
        current_step: Current workflow step (1-5)
        script: Generated script JSON
        storyboard: Storyboard configuration JSON
        metadata: Additional metadata JSON
        target_duration: Target video duration in seconds
        aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1)
        video_provider: Selected video generation provider
        image_provider: Selected image generation provider
        output_video_url: Final rendered video URL
        output_thumbnail_url: Video thumbnail URL
        output_duration: Actual video duration
        error_message: Error message if failed
        completed_at: Completion timestamp

    Relationships:
        brand: One-to-One relationship to Brand
        product: One-to-One relationship to Product
        reference_analysis: One-to-One relationship to ReferenceAnalysis
        scene_images: One-to-Many relationship to SceneImage
        scene_videos: One-to-Many relationship to SceneVideo
        storyboards: One-to-Many relationship to Storyboard
    """

    __tablename__ = "video_projects"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    brand_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reference_analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("reference_analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="draft",
        index=True,
    )

    current_step: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    script: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )

    storyboard: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )

    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    target_duration: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    aspect_ratio: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="16:9",
    )

    video_provider: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    image_provider: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    output_video_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    output_thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    output_duration: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Relationships
    brand: Mapped["Brand"] = relationship(
        "Brand",
        lazy="selectin",
    )

    product: Mapped["Product"] = relationship(
        "Product",
        lazy="selectin",
    )

    reference_analysis: Mapped[Optional["ReferenceAnalysis"]] = relationship(
        "ReferenceAnalysis",
        lazy="selectin",
    )

    scene_images: Mapped[List["SceneImage"]] = relationship(
        "SceneImage",
        back_populates="video_project",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="SceneImage.scene_number",
    )

    scene_videos: Mapped[List["SceneVideo"]] = relationship(
        "SceneVideo",
        back_populates="video_project",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="SceneVideo.scene_number",
    )

    storyboards: Mapped[List["Storyboard"]] = relationship(
        "Storyboard",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="Storyboard.video_project_id",
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_video_projects_brand_status", "brand_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<VideoProject(id={self.id!r}, title={self.title!r}, status={self.status!r})>"


__all__ = ["VideoProject"]
