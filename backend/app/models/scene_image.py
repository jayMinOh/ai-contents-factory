"""
Scene Image ORM model for the AI Video Marketing Platform.

Represents an image asset for a specific scene in a video project,
supporting both user uploads and AI-generated images.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.video_project import VideoProject


class SceneImage(Base, TimestampMixin):
    """
    Scene Image model representing an image for a video scene.

    Attributes:
        id: UUID string primary key
        video_project_id: Foreign key to VideoProject
        scene_number: Scene number (0-based index)
        source: Image source (uploaded, ai_generated)
        image_url: URL to the stored image
        thumbnail_url: URL to thumbnail image
        generation_prompt: AI generation prompt if applicable
        generation_provider: AI provider used (gemini_imagen, dalle, etc.)
        generation_params: Generation parameters JSON
        generation_duration_ms: Generation time in milliseconds
        scene_segment_type: Type of scene (hook, problem, solution, etc.)
        scene_description: Description of the scene
        duration_seconds: Scene duration in seconds
        version: Version number for this scene
        is_active: Whether this is the active version
        previous_version_id: Link to previous version
    """

    __tablename__ = "scene_images"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    video_project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("video_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scene_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    generation_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    generation_provider: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    generation_params: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )

    generation_duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    scene_segment_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    scene_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    previous_version_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
    )

    # Relationships
    video_project: Mapped["VideoProject"] = relationship(
        "VideoProject",
        back_populates="scene_images",
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_scene_images_project_scene", "video_project_id", "scene_number"),
        Index("ix_scene_images_project_active", "video_project_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<SceneImage(id={self.id!r}, scene={self.scene_number}, source={self.source!r})>"


__all__ = ["SceneImage"]
