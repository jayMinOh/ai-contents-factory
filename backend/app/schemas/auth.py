"""
Authentication Pydantic schemas for request/response validation.
"""

from typing import Optional

from pydantic import BaseModel

from app.schemas.user import UserResponse


class GoogleAuthRequest(BaseModel):
    """Request schema for Google OAuth authentication."""
    code: str
    redirect_uri: Optional[str] = None


class AuthResponse(BaseModel):
    """Response schema for authentication."""
    user: UserResponse
    message: str


class LogoutResponse(BaseModel):
    """Response schema for logout."""
    message: str


__all__ = [
    "GoogleAuthRequest",
    "AuthResponse",
    "LogoutResponse",
]
