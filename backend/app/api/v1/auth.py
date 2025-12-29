"""
Authentication API endpoints for Google OAuth.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.auth import AuthResponse, GoogleAuthRequest, LogoutResponse
from app.schemas.user import UserCreate, UserResponse
from app.services import auth_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=AuthResponse)
async def google_auth(
    request: GoogleAuthRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate with Google OAuth.

    1. Exchange authorization code for tokens
    2. Get user info from Google
    3. Create or update user in database
    4. Set JWT cookie
    5. Return user info
    """
    # Default redirect URI
    redirect_uri = request.redirect_uri or f"{settings.FRONTEND_URL}/login"

    try:
        # Exchange code for tokens
        token_data = await auth_service.exchange_google_code(
            code=request.code,
            redirect_uri=redirect_uri,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Get user info from Google
    try:
        google_user = await auth_service.get_google_user_info(token_data["access_token"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Check if user exists
    user = await user_service.get_user_by_google_id(db, google_user["sub"])

    if user:
        # Update last login
        user = await user_service.update_last_login(db, user)
        message = "Login successful"
    else:
        # Check if this is the first user
        user_count = await user_service.get_user_count(db)
        is_first_user = user_count == 0

        # Create new user
        user_data = UserCreate(
            email=google_user["email"],
            name=google_user.get("name", google_user["email"]),
            picture_url=google_user.get("picture"),
            google_id=google_user["sub"],
        )
        user = await user_service.create_user(db, user_data, is_first_user=is_first_user)

        if is_first_user:
            message = "Welcome! You are the first user and have been granted admin access."
        else:
            message = "Registration successful. Please wait for admin approval."

    # Create JWT token
    access_token = auth_service.create_access_token(user.id)

    # Set HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        message=message,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user info."""
    return UserResponse.model_validate(current_user)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user_optional),
):
    """Logout by clearing the access token cookie."""
    response.delete_cookie(
        key="access_token",
        path="/",
    )
    return LogoutResponse(message="Logged out successfully")


__all__ = ["router"]
