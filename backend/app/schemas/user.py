"""
User Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    name: str
    picture_url: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user (internal use)."""
    google_id: str
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.PENDING


class UserUpdate(BaseModel):
    """Schema for updating user (admin use)."""
    name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: str
    google_id: str
    role: UserRole
    status: UserStatus
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Schema for user list item (admin panel)."""
    id: str
    email: str
    name: str
    picture_url: Optional[str] = None
    role: UserRole
    status: UserStatus
    last_login: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: str  # user_id
    exp: datetime
    iat: datetime


__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "TokenPayload",
]
