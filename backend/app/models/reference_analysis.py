"""
ReferenceAnalysis ORM model for storing video analysis results.

Stores the complete analysis results from Gemini for reference videos,
enabling reuse in Video Studio without re-analyzing.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class ReferenceAnalysis(Base, TimestampMixin):
    """
    ReferenceAnalysis model for storing video analysis results.

    Attributes:
        id: UUID string primary key
        source_url: Original video URL (YouTube, etc.)
        title: User-defined title for this analysis
        status: Analysis status (pending, analyzing, completed, failed)
        duration: Video duration in seconds
        thumbnail_url: Video thumbnail URL
        segments: Timeline segments (hook, problem, solution, etc.)
        hook_points: Hooking techniques identified
        edge_points: Differentiation elements
        emotional_triggers: Emotional triggers used
        pain_points: Pain points addressed
        application_points: Applicable elements
        selling_points: Persuasion techniques
        cta_analysis: Call-to-action analysis
        structure_pattern: Overall video structure pattern
        recommendations: Actionable recommendations
        transcript: Video transcript/narration
        tags: User-defined tags for filtering
        notes: User notes
        error_message: Error message if analysis failed
    """

    __tablename__ = "reference_analyses"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    source_url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    duration: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Analysis results (JSON fields)
    segments: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    hook_points: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    edge_points: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    emotional_triggers: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    pain_points: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    application_points: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    selling_points: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    cta_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    structure_pattern: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    recommendations: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    transcript: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # User metadata
    tags: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<ReferenceAnalysis(id={self.id!r}, title={self.title!r}, status={self.status!r})>"


__all__ = ["ReferenceAnalysis"]
