"""
User ORM model for the AI Video Marketing Platform.

Represents a user entity with Google OAuth authentication,
role-based access control, and approval status management.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"


class UserStatus(str, enum.Enum):
    """User approval status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base, TimestampMixin):
    """
    User model for authentication and authorization.

    Attributes:
        id: UUID string primary key
        email: User email from Google (unique, indexed)
        name: Display name from Google
        picture_url: Profile picture URL from Google
        google_id: Google OAuth sub claim (unique)
        role: User role (admin or user)
        status: Approval status (pending, approved, rejected)
        last_login: Last login timestamp
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    picture_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    google_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.USER,
    )

    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus),
        nullable=False,
        default=UserStatus.PENDING,
    )

    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Index for status queries (admin panel)
    __table_args__ = (
        Index("ix_users_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id!r}, email={self.email!r}, role={self.role!r}, status={self.status!r})>"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN

    @property
    def is_approved(self) -> bool:
        """Check if user is approved."""
        return self.status == UserStatus.APPROVED


__all__ = ["User", "UserRole", "UserStatus"]
