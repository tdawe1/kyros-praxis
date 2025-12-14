"""Authentication utilities for JWT token generation and validation.

This module provides authentication functions using JWT tokens with HS256 algorithm
and bcrypt password hashing. Adapted from legacy orchestrator for CrewAI API.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .core.config import settings
from .db.session import get_session
from .db.models import User
from .models import TokenData


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)  # Optional auth by default


def get_jwt_settings() -> tuple[str, str, int]:
    """Get JWT configuration from settings.
    
    Returns:
        Tuple of (secret_key, algorithm, expiration_minutes)
        
    Raises:
        ValueError: If JWT_SECRET_KEY is not set or too short
    """
    secret_key = settings.JWT_SECRET_KEY
    if not secret_key or len(secret_key) < 32:
        raise ValueError(
            "JWT_SECRET_KEY must be set in environment and at least 32 characters. "
            "Generate one with: openssl rand -hex 32"
        )
    algorithm = settings.JWT_ALGORITHM
    expire_minutes = settings.JWT_EXPIRE_MINUTES
    return secret_key, algorithm, expire_minutes


async def get_current_user_from_token(token: str, session: AsyncSession, allowed_types: list[str] = None) -> Optional[User]:
    """
    Validate JWT token and return user (without raising exceptions).
    
    Utility function for non-HTTP contexts like WebSocket authentication.
    
    Args:
        token: JWT token string
        session: Database session
        allowed_types: List of allowed token types (default: ["access", "ws"])
        
    Returns:
        User object if valid, None otherwise
    """
    if allowed_types is None:
        allowed_types = ["access", "ws"]
        
    try:
        secret_key, algorithm, _ = get_jwt_settings()
        
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm]
        )
        email: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        
        if email is None:
            return None
        
        # Validate token type
        if token_type not in allowed_types:
            return None
        
        # Fetch user from database
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalars().first()
        
        if user and user.active:
            return user
        return None
    except JWTError:
        return None
    except Exception:
        return None


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against its hashed version.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against
        
    Returns:
        True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Retrieve a user from the database by email address.
    
    Args:
        session: Database session
        email: User's email address
        
    Returns:
        User object if found, None otherwise
    """
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    """Retrieve a user from the database by username.
    
    Args:
        session: Database session
        username: User's username
        
    Returns:
        User object if found, None otherwise
    """
    result = await session.execute(select(User).where(User.username == username))
    return result.scalars().first()


async def authenticate_user(session: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password.
    
    Args:
        session: Database session
        email: User's email address
        password: User's plain text password
        
    Returns:
        User object if authentication successful, None otherwise
    """
    user = await get_user_by_email(session, email)
    if not user:
        return None
    if not user.active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, token_type: str = "access") -> str:
    """Create a JWT access token with standard claims.
    
    Args:
        data: Dictionary containing token payload data (e.g., {"sub": user_email})
        expires_delta: Optional custom expiration time
        token_type: Type of token ('access' or 'refresh')
        
    Returns:
        Encoded JWT token string
    """
    secret_key, algorithm, default_expire = get_jwt_settings()
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=default_expire)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "kyros-api",
        "type": token_type  # Track token type for validation
    })
    
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with longer expiration.
    
    Args:
        data: Dictionary containing token payload data
        
    Returns:
        Encoded refresh token
    """
    expires_delta = timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    return create_access_token(data, expires_delta, token_type="refresh")


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> Optional[User]:
    """Extract and validate the current user from JWT token or httpOnly cookie.
    
    This dependency is optional - returns None if no credentials provided.
    Use `get_current_user_required` for endpoints that require authentication.
    
    Tries in order:
    1. Authorization header (Bearer token) - for API clients
    2. HttpOnly cookie (access_token) - for browser clients
    
    Args:
        credentials: HTTP Authorization credentials from request (optional)
        session: Database session
        request: FastAPI request object for cookie access
        
    Returns:
        User object for the authenticated user, or None if no auth provided
        
    Raises:
        HTTPException: If token is provided but invalid
    """
    token = None
    
    # Try Authorization header first (API clients, backward compatibility)
    if credentials:
        token = credentials.credentials
    # Fall back to httpOnly cookie (browser clients)
    else:
        token = request.cookies.get("access_token")
    
    if not token:
        return None
    
    secret_key, algorithm, _ = get_jwt_settings()
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
        )
        email: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        
        if email is None:
            raise credentials_exception
        
        # Enforce token type - only "access" tokens allowed for regular API endpoints
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type for this endpoint",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(session, email=token_data.email)
    if user is None:
        raise credentials_exception
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_user_required(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """Require authentication - raises 401 if no valid user.
    
    Args:
        user: User from get_current_user dependency
        
    Returns:
        User object
        
    Raises:
        HTTPException: 401 if not authenticated
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_admin(
    current_user: User = Depends(get_current_user_required),
) -> User:
    """Require admin role.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        User object if admin
        
    Raises:
        HTTPException: 403 if not admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
