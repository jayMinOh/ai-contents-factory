"""
Generated Image ORM model for the AI Video Marketing Platform.

Represents an AI-generated image for an image project.
Supports multiple variants per slide for user selection.
Supports step-by-step generation with approval workflow and reference image system.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.image_project import ImageProject


class GeneratedImage(Base, TimestampMixin):
    """
    Generated Image model representing an AI-generated image.

    Attributes:
        id: UUID string primary key
        image_project_id: Foreign key to ImageProject
        slide_number: Slide number (1-based, for carousel type)
        variant_index: Variant index (0-3 for 4 variants per slide)
        image_url: URL to the generated image
        prompt: Prompt used for generation
        is_selected: Whether this variant is selected by user
        approval_status: Approval status (pending, approved, rejected)
        is_reference_image: Whether this image is set as reference for style/mood
        generation_provider: AI provider used (gemini_imagen, etc.)
        generation_duration_ms: Generation time in milliseconds

    Relationships:
        image_project: Many-to-One relationship to ImageProject
    """

    __tablename__ = "generated_images"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    image_project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("image_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    slide_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    variant_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    is_selected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Approval status for step-by-step generation workflow
    # Values: 'pending', 'approved', 'rejected'
    approval_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    # Flag indicating this image is set as reference for style/mood consistency
    is_reference_image: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    generation_provider: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    generation_duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Relationships
    # foreign_keys specified as string to disambiguate multiple FK paths
    # (image_project_id -> ImageProject, and ImageProject.reference_image_id -> GeneratedImage)
    image_project: Mapped["ImageProject"] = relationship(
        "ImageProject",
        back_populates="generated_images",
        foreign_keys="[GeneratedImage.image_project_id]",
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_generated_images_project_slide", "image_project_id", "slide_number"),
        Index("ix_generated_images_project_selected", "image_project_id", "is_selected"),
    )

    def __repr__(self) -> str:
        return f"<GeneratedImage(id={self.id!r}, slide={self.slide_number}, variant={self.variant_index})>"


__all__ = ["GeneratedImage"]
