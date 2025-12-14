"""Authentication endpoints for user registration and login."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_user_by_email,
    get_user_by_username,
    hash_password,
)
from ..core.config import settings
from ..db.models import User
from ..db.session import get_session
from ..models import LoginRequest, Token, UserCreate, UserResponse


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    """Register a new user account.
    
    Creates a new user with hashed password. Username and email must be unique.
    
    Args:
        user_data: User registration data (username, email, password)
        session: Database session
        
    Returns:
        UserResponse: Created user information (without password)
        
    Raises:
        HTTPException: 400 if username or email already exists
    """
    # Check if username already exists
    existing_user = await get_user_by_username(session, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await get_user_by_email(session, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        id=str(uuid4()),  # Generate ID explicitly for immediate availability
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role="user",
        active=True,
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        active=user.active,
        created_at=user.created_at.isoformat(),
    )


@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    """Authenticate user and return JWT tokens with httpOnly cookie.
    
    Returns both access and refresh tokens. Access token is also set as
    httpOnly cookie for browser clients.
    
    Args:
        credentials: Login credentials (email, password)
        response: FastAPI response object (for setting cookies)
        session: Database session
        
    Returns:
        Token: JWT access token, refresh token, and token type
        
    Raises:
        HTTPException: 401 if authentication fails
    """
    user = await authenticate_user(session, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token (short-lived: 15 minutes)
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    
    # Create refresh token (long-lived: 7 days)
    refresh_token = create_refresh_token(data={"sub": user.email, "user_id": user.id})
    
    # Set access token as httpOnly cookie (XSS protection)
    is_production = settings.KYROS_ENV == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=settings.COOKIE_HTTPONLY,  # Prevent JavaScript access
        secure=settings.COOKIE_SECURE and is_production,  # HTTPS only in production
        samesite=settings.COOKIE_SAMESITE,  # CSRF protection
        max_age=settings.JWT_EXPIRE_MINUTES * 60,  # Convert minutes to seconds
        domain=settings.COOKIE_DOMAIN,
    )
    
    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE and is_production,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 60 * 60,  # Convert days to seconds
        domain=settings.COOKIE_DOMAIN,
    )
    
    return Token(access_token=access_token, token_type="bearer", refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user information.
    
    Args:
        current_user: Authenticated user from JWT token
        
    Returns:
        UserResponse: Current user information
        
    Raises:
        HTTPException: 401 if not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        active=current_user.active,
        created_at=current_user.created_at.isoformat(),
    )
