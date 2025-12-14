"""
Unified session management for all authentication providers.

Creates and manages user sessions regardless of auth method.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Response

from ..core.config import settings
from ..db.models import User

# Import from auth.py module (separate from auth package)
import app.auth as auth_module


async def create_session(
    user: User,
    provider: str = "password",
    response: Optional[Response] = None,
    expires_delta: Optional[timedelta] = None
) -> dict:
    """
    Create authenticated session for user.
    
    Works for any authentication provider (password, OAuth, etc.).
    Sets httpOnly cookie if response provided.
    
    Args:
        user: Authenticated user
        provider: Auth provider name ('password', 'google', 'github', etc.)
        response: FastAPI response object (optional, for cookie)
        expires_delta: Custom token expiration
        
    Returns:
        Session data with token and user info
    """
    # Create access token
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "provider": provider
    }
    
    token = auth_module.create_access_token(token_data, expires_delta)
    
    # Set httpOnly cookie if response provided
    if response:
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=settings.KYROS_ENV == "production",
            samesite="strict",
            max_age=int(expires_delta.total_seconds())
        )
    
    # Return session data
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": int(expires_delta.total_seconds()),
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "auth_provider": provider
        }
    }


async def destroy_session(response: Response) -> dict:
    """
    Destroy user session.
    
    Args:
        response: FastAPI response object
        
    Returns:
        Logout confirmation
    """
    # Clear cookie
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=settings.KYROS_ENV == "production",
        samesite="strict"
    )
    
    # TODO: Add token to blacklist (Redis) when implementing refresh tokens
    
    return {"message": "Logged out successfully"}
