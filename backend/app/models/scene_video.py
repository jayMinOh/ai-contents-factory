"""
Scene Video ORM model for the AI Video Marketing Platform.

Represents a video asset for a specific scene in a video project,
supporting AI-generated videos from various providers.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.video_project import VideoProject


class SceneVideo(Base, TimestampMixin):
    """
    Scene Video model representing a video for a video scene.

    Attributes:
        id: UUID string primary key
        video_project_id: Foreign key to VideoProject
        scene_number: Scene number (0-based index)
        source: Video generation source (veo, mock, etc.)
        video_url: URL to the stored video
        thumbnail_url: URL to video thumbnail
        generation_prompt: AI generation prompt used
        generation_provider: AI provider used (veo, runway, etc.)
        generation_params: Generation parameters JSON
        generation_duration_ms: Generation time in milliseconds
        scene_segment_type: Type of scene (hook, problem, solution, etc.)
        duration_seconds: Actual video duration in seconds
        version: Version number for this scene
        is_active: Whether this is the active version
        operation_id: Async generation operation tracking ID
        status: Generation status (pending, processing, completed, failed)
        error_message: Error details if generation failed
    """

    __tablename__ = "scene_videos"

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

    video_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
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

    operation_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    video_project: Mapped["VideoProject"] = relationship(
        "VideoProject",
        back_populates="scene_videos",
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_scene_videos_project_scene", "video_project_id", "scene_number"),
        Index("ix_scene_videos_project_active", "video_project_id", "is_active"),
        Index("ix_scene_videos_status", "status"),
        Index("ix_scene_videos_operation", "operation_id"),
    )

    def __repr__(self) -> str:
        return f"<SceneVideo(id={self.id!r}, scene={self.scene_number}, status={self.status!r})>"


__all__ = ["SceneVideo"]
