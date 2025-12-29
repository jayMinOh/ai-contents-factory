"""
User service for CRUD operations.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserUpdate


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_google_id(db: AsyncSession, google_id: str) -> Optional[User]:
    """Get user by Google ID."""
    result = await db.execute(select(User).where(User.google_id == google_id))
    return result.scalar_one_or_none()


async def get_user_count(db: AsyncSession) -> int:
    """Get total user count."""
    result = await db.execute(select(func.count()).select_from(User))
    return result.scalar() or 0


async def create_user(
    db: AsyncSession,
    user_data: UserCreate,
    is_first_user: bool = False,
) -> User:
    """
    Create a new user.
    First user becomes admin and is auto-approved.
    """
    user = User(
        id=str(uuid.uuid4()),
        email=user_data.email,
        name=user_data.name,
        picture_url=user_data.picture_url,
        google_id=user_data.google_id,
        role=UserRole.ADMIN if is_first_user else UserRole.USER,
        status=UserStatus.APPROVED if is_first_user else UserStatus.PENDING,
        last_login=datetime.utcnow(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession,
    user: User,
    user_data: UserUpdate,
) -> User:
    """Update user fields."""
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def update_last_login(db: AsyncSession, user: User) -> User:
    """Update user's last login timestamp."""
    user.last_login = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user


async def list_users(
    db: AsyncSession,
    status_filter: Optional[UserStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[User]:
    """List all users with optional status filter."""
    query = select(User).order_by(User.created_at.desc())

    if status_filter:
        query = query.where(User.status == status_filter)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def approve_user(db: AsyncSession, user: User) -> User:
    """Approve a pending user."""
    user.status = UserStatus.APPROVED
    await db.commit()
    await db.refresh(user)
    return user


async def reject_user(db: AsyncSession, user: User) -> User:
    """Reject a pending user."""
    user.status = UserStatus.REJECTED
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    """Delete a user."""
    await db.delete(user)
    await db.commit()


__all__ = [
    "get_user_by_id",
    "get_user_by_email",
    "get_user_by_google_id",
    "get_user_count",
    "create_user",
    "update_user",
    "update_last_login",
    "list_users",
    "approve_user",
    "reject_user",
    "delete_user",
]
