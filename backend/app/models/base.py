"""
Base model with timestamp mixin for all SQLAlchemy ORM models.

Provides common timestamp fields (created_at, updated_at) that are
automatically managed by the database.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TimestampMixin:
    """
    Mixin providing created_at and updated_at timestamp fields.

    - created_at: Set automatically on insert using server default
    - updated_at: Set automatically on insert and update
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


__all__ = ["Base", "TimestampMixin"]
