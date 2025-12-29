"""
Authentication dependencies for FastAPI routes.

Provides dependency injection functions for:
- Extracting current user from JWT cookie
- Requiring approved users
- Requiring admin role
"""

from datetime import datetime
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole, UserStatus


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    access_token: Optional[str] = Cookie(default=None),
) -> Optional[User]:
    """
    Extract current user from JWT cookie if present.
    Returns None if no valid token found.
    """
    if not access_token:
        return None

    try:
        payload = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user


async def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """
    Require authenticated user.
    Raises 401 if not authenticated.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_approved_user(
    user: User = Depends(get_current_user),
) -> User:
    """
    Require authenticated AND approved user.
    Raises 401 if not authenticated.
    Raises 403 if not approved.
    """
    if user.status == UserStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending approval",
        )
    if user.status == UserStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been rejected",
        )
    return user


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    """
    Require admin role.
    Raises 401 if not authenticated.
    Raises 403 if not admin.
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "require_approved_user",
    "require_admin",
]
