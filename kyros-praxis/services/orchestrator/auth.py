"""Authentication module for the Orchestrator API.

This module handles JWT token generation, validation, and user authentication
using HS512 algorithm with bcrypt password hashing.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import User

SECRET_KEY = (os.getenv("SECRET_KEY") or "").strip()
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise ValueError(
        "SECRET_KEY must be set and at least 32 characters for HS256"
    )
ALGORITHM = "HS512"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Require credentials; FastAPI will raise 401 if the Authorization header is
# missing or malformed instead of returning a 500 later when accessing
# credentials.credentials.
oauth2_scheme = HTTPBearer(auto_error=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class Login(BaseModel):
    email: str
    password: str


class TokenData(BaseModel):
    email: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against its hashed version.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against

    Returns:
        True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db: Session, email: str) -> Optional[User]:
    """Retrieve a user from the database by email address.

    Args:
        db: Database session
        email: User's email address

    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str):
    """Authenticate a user with email and password.

    Args:
        db: Database session
        email: User's email address
        password: User's plain text password

    Returns:
        User object if authentication successful, False otherwise
    """
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token with standard claims.

    Args:
        data: Dictionary containing token payload data (e.g., {"sub": user_email})
        expires_delta: Optional custom expiration time, defaults to ACCESS_TOKEN_EXPIRE_MINUTES

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    # Include standard claims required by get_current_user
    to_encode.update(
        {
            "exp": expire,
            "aud": "api",
            "iss": "https://orchestrator.local",
        }
    )
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Extract and validate the current user from JWT token.

    Args:
        credentials: HTTP Authorization credentials from request
        db: Database session

    Returns:
        User object for the authenticated user

    Raises:
        HTTPException: If token is invalid or user doesn't exist
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience="api",
            issuer="https://orchestrator.local",
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user
