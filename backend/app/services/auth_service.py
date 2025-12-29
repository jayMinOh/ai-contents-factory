"""
Authentication service for Google OAuth and JWT handling.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import httpx
from jose import jwt

from app.core.config import settings

logger = logging.getLogger(__name__)


# Google OAuth endpoints
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


async def exchange_google_code(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Exchange Google authorization code for access token.

    Args:
        code: Authorization code from Google OAuth
        redirect_uri: Redirect URI used in the OAuth flow

    Returns:
        Token response containing access_token, refresh_token, etc.

    Raises:
        ValueError: If token exchange fails
    """
    logger.info(f"Exchanging Google code, redirect_uri: {redirect_uri}")
    logger.info(f"Client ID: {settings.GOOGLE_CLIENT_ID[:20]}...")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )

        if response.status_code != 200:
            error_data = response.json()
            logger.error(f"Google token exchange failed: {error_data}")
            raise ValueError(f"Google token exchange failed: {error_data}")

        logger.info("Google token exchange successful")
        return response.json()


async def get_google_user_info(access_token: str) -> Dict[str, Any]:
    """
    Get user info from Google using access token.

    Args:
        access_token: Google OAuth access token

    Returns:
        User info containing sub, email, name, picture, etc.

    Raises:
        ValueError: If user info request fails
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status_code != 200:
            raise ValueError("Failed to get Google user info")

        return response.json()


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        user_id: User ID to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except Exception:
        return None


def get_google_oauth_url(redirect_uri: str, state: Optional[str] = None) -> str:
    """
    Generate Google OAuth authorization URL.

    Args:
        redirect_uri: Redirect URI after OAuth
        state: Optional state parameter for CSRF protection

    Returns:
        Google OAuth authorization URL
    """
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }

    if state:
        params["state"] = state

    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"


__all__ = [
    "exchange_google_code",
    "get_google_user_info",
    "create_access_token",
    "verify_access_token",
    "get_google_oauth_url",
]
