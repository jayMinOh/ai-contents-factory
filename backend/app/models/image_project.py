"""
Image Project ORM model for the AI Video Marketing Platform.

Represents an image project entity for AI-powered image generation workflow.
Supports single image, carousel, and story content types.
Supports step-by-step and bulk generation modes with reference image system.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.generated_image import GeneratedImage
    from app.models.product import Product
    from app.models.reference_analysis import ReferenceAnalysis


class ImageProject(Base, TimestampMixin):
    """
    Image Project model representing an image generation workflow.

    Attributes:
        id: UUID string primary key
        title: Project title (auto-generated if not provided)
        content_type: Type of content (single, carousel, story)
        purpose: Purpose of content (ad, info, lifestyle)
        method: Generation method (reference, prompt)
        generation_mode: Generation workflow mode (step_by_step, bulk)
        reference_image_id: Foreign key to GeneratedImage used as reference
        brand_id: Foreign key to Brand (optional)
        product_id: Foreign key to Product (optional)
        reference_analysis_id: Foreign key to ReferenceAnalysis (optional)
        storyboard_data: Storyboard JSON data (for carousel type)
        prompt: User prompt for generation
        aspect_ratio: Image aspect ratio (1:1, 4:5, 9:16, etc.)
        status: Project status (draft, generating, completed, failed)
        current_step: Current workflow step
        current_slide: Current slide being generated (for step-by-step mode)
        error_message: Error message if failed
        completed_at: Completion timestamp

    Relationships:
        brand: One-to-One relationship to Brand
        product: One-to-One relationship to Product
        reference_analysis: One-to-One relationship to ReferenceAnalysis
        generated_images: One-to-Many relationship to GeneratedImage
    """

    __tablename__ = "image_projects"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    content_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    purpose: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Generation mode: 'step_by_step' or 'bulk'
    # step_by_step: Generate one scene, approve, use as reference for next
    # bulk: Generate all scenes at once
    generation_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="bulk",
    )

    # Reference image for style/mood consistency
    # Points to a GeneratedImage that has been approved
    reference_image_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("generated_images.id", ondelete="SET NULL"),
        nullable=True,
    )

    brand_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("brands.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    product_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    reference_analysis_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("reference_analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    storyboard_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )

    prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    aspect_ratio: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="1:1",
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

    # Current slide being generated (for step-by-step mode)
    current_slide: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
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
    brand: Mapped[Optional["Brand"]] = relationship(
        "Brand",
        lazy="selectin",
    )

    product: Mapped[Optional["Product"]] = relationship(
        "Product",
        lazy="selectin",
    )

    reference_analysis: Mapped[Optional["ReferenceAnalysis"]] = relationship(
        "ReferenceAnalysis",
        lazy="selectin",
    )

    # Reference image for style/mood consistency (foreign_keys needed to avoid ambiguity)
    reference_image: Mapped[Optional["GeneratedImage"]] = relationship(
        "GeneratedImage",
        foreign_keys=[reference_image_id],
        lazy="selectin",
        post_update=True,  # Needed to break circular dependency during inserts
    )

    generated_images: Mapped[List["GeneratedImage"]] = relationship(
        "GeneratedImage",
        back_populates="image_project",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="[GeneratedImage.slide_number, GeneratedImage.variant_index]",
        foreign_keys="[GeneratedImage.image_project_id]",
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_image_projects_brand_status", "brand_id", "status"),
        Index("ix_image_projects_content_type_status", "content_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<ImageProject(id={self.id!r}, title={self.title!r}, status={self.status!r})>"


__all__ = ["ImageProject"]
