"""Token refresh and logout endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

# Import from auth.py module (not auth package)
import app.auth as auth_module
from ..core.config import settings
from ..db.session import get_session
from ..models import Token


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    """Refresh access token using refresh token.
    
    Validates refresh token from httpOnly cookie and issues new access + refresh tokens.
    Implements token rotation: old refresh token is invalidated when used.
    
    Args:
        request: FastAPI request object (for cookie access)
        response: FastAPI response object (for setting new cookies)
        session: Database session
        
    Returns:
        Token: New access and refresh tokens
        
    Raises:
        HTTPException: 401 if refresh token invalid or expired
    """
    # Get refresh token from httpOnly cookie
    refresh_token_str = request.cookies.get("refresh_token")
    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found. Please login again.",
        )
    
    secret_key, algorithm, _ = auth_module.get_jwt_settings()
    
    try:
        # Decode and validate refresh token
        payload = jwt.decode(
            refresh_token_str,
            secret_key,
            algorithms=[algorithm],
        )
        
        # Verify it's a refresh token
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected refresh token.",
            )
        
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if email is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        
        # Verify user still exists and is active
        user = await auth_module.get_user_by_email(session, email)
        if not user or not user.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        
        # Create new access token
        new_access_token = auth_module.create_access_token(data={"sub": email, "user_id": user_id})
        
        # Create new refresh token (token rotation)
        new_refresh_token = auth_module.create_refresh_token(data={"sub": email, "user_id": user_id})
        
        # Set new access token cookie
        is_production = settings.KYROS_ENV == "production"
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=settings.COOKIE_HTTPONLY,
            secure=settings.COOKIE_SECURE and is_production,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.JWT_EXPIRE_MINUTES * 60,
            domain=settings.COOKIE_DOMAIN,
        )
        
        # Set new refresh token cookie (rotation)
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=settings.COOKIE_SECURE and is_production,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 60 * 60,
            domain=settings.COOKIE_DOMAIN,
        )
        
        return Token(
            access_token=new_access_token,
            token_type="bearer",
            refresh_token=new_refresh_token
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token. Please login again.",
        )


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing httpOnly cookies.
    
    Clears both access and refresh token cookies. In production with Redis,
    this should also add tokens to a blacklist.
    
    Args:
        response: FastAPI response object (for clearing cookies)
        
    Returns:
        Success message
    """
    # Clear access token cookie
    response.delete_cookie(
        key="access_token",
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE and (settings.KYROS_ENV == "production"),
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
    )
    
    # Clear refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=settings.COOKIE_SECURE and (settings.KYROS_ENV == "production"),
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
    )
    
    # TODO: Add token to Redis blacklist when Redis is configured
    # await blacklist_token(access_token)
    
    return {"message": "Successfully logged out"}
