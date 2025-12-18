"""
Storyboard ORM model for AI Video Marketing Platform.

Represents a storyboard entity that contains scenes for video generation.
Each storyboard is associated with a VideoProject and can optionally reference
a ReferenceAnalysis for structure guidance.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Float, ForeignKey, Index, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


def default_scenes() -> List[Dict[str, Any]]:
    """Default factory for scenes JSON field."""
    return []


class Storyboard(Base, TimestampMixin):
    """
    Storyboard model representing video scenes and structure.

    Attributes:
        id: UUID string primary key
        video_project_id: Foreign key to VideoProject (required)
        generation_mode: "reference_structure" | "ai_optimized" (required)
        source_reference_analysis_id: Foreign key to ReferenceAnalysis (optional)
        scenes: JSON array of Scene objects (default: [])
        total_duration_seconds: Expected total video duration in seconds (optional)
        version: Version number for storyboard (default: 1)
        is_active: Whether this is the active version (default: True)
        previous_version_id: Self-reference to previous version (optional)
        created_at: Timestamp when created (from TimestampMixin)
        updated_at: Timestamp when last updated (from TimestampMixin)
    """

    __tablename__ = "storyboards"

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

    generation_mode: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    source_reference_analysis_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("reference_analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    scenes: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=default_scenes,
    )

    total_duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    previous_version_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("storyboards.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_storyboards_video_project_active", "video_project_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Storyboard(id={self.id!r}, video_project_id={self.video_project_id!r}, generation_mode={self.generation_mode!r})>"


__all__ = ["Storyboard"]
