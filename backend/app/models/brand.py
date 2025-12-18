"""
Brand ORM model for the AI Video Marketing Platform.

Represents a brand entity with associated metadata including
target audience, tone, unique selling points, and related products.
"""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.product import Product


class Brand(Base, TimestampMixin):
    """
    Brand model representing a company or product line.

    Attributes:
        id: UUID string primary key
        name: Brand name (required, indexed)
        description: Detailed brand description
        logo_url: URL to brand logo image
        target_audience: Description of target demographic
        tone_and_manner: Brand voice style (casual, professional, etc.)
        usp: Unique Selling Point
        keywords: List of keywords associated with the brand
        industry: Industry category
        products: Related products (one-to-many relationship)
    """

    __tablename__ = "brands"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    logo_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    target_audience: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    tone_and_manner: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    usp: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    keywords: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    industry: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Relationship: One brand has many products
    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="brand",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Brand(id={self.id!r}, name={self.name!r})>"


__all__ = ["Brand"]
