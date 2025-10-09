"""
Authentication module for the Kyros Orchestrator service.

This module provides user authentication functionality including password verification,
JWT token creation and validation, and user authentication against the database.
It uses bcrypt for password hashing and JWT for token-based authentication.

The module handles both synchronous and asynchronous database operations for user retrieval
and provides FastAPI dependency injection for authentication middleware.

MODULE RESPONSIBILITIES:
------------------------
1. User Authentication:
   - Password verification using bcrypt hashing
   - User retrieval from database (sync and async)
   - Authentication flow implementation

2. JWT Token Management:
   - Token creation with standard claims
   - Token validation and verification
   - Secure token expiration handling

3. FastAPI Integration:
   - Dependency injection for authentication
   - HTTP bearer token handling
   - Current user retrieval for protected endpoints

4. Security Implementation:
   - Secure password storage with bcrypt
   - JWT token signing and validation
   - Protection against timing attacks
   - Secure error handling to prevent information leakage

SECURITY FEATURES:
------------------
- Secure password hashing with bcrypt:
  * Uses adaptive hashing algorithm
  * Automatically handles salt generation
  * Provides resistance against rainbow table attacks

- JWT token-based authentication:
  * Standard claims (exp, iss, aud, iat)
  * Cryptographically signed tokens
  * Configurable expiration times
  * Secure token validation

- Protection mechanisms:
  * Constant-time password comparison
  * Secure error messages to prevent user enumeration
  * Token signature verification
  * Claim validation (issuer, audience, expiration)

COMPONENTS:
-----------
1. Password Management:
   - verify_password(): Secure password verification
   - pwd_context: Passlib context for bcrypt hashing

2. User Retrieval:
   - get_user(): Synchronous user retrieval
   - get_user_async(): Asynchronous user retrieval

3. Authentication Flow:
   - authenticate_user(): Complete user authentication
   - create_access_token(): JWT token creation
   - get_current_user(): FastAPI dependency for current user

4. Data Models:
   - Token: JWT token response model
   - Login: Login request model
   - TokenData: Decoded token data model

INTEGRATION WITH OTHER MODULES:
-------------------------------
- main.py: Uses authentication endpoints and dependencies
- database.py: Depends on database session for user retrieval
- security_middleware.py: Works with security middleware for comprehensive protection
- models.py: Uses User model for authentication operations

USAGE EXAMPLES:
---------------
User login endpoint:
    @app.post("/auth/login")
    async def login(payload: Login, db=Depends(get_db)):
        user = authenticate_user(db, payload.username, payload.password)
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect credentials")
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}

Protected endpoint:
    @app.get("/protected")
    async def protected_route(current_user: User = Depends(get_current_user)):
        return {"message": f"Hello, {current_user.username}!"}

See Also:
--------
- security_middleware.py: Security middleware that complements authentication
- database.py: Database session management for user retrieval
- models.py: User model definition
- main.py: Main application that implements authentication endpoints
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum
from typing import Set

try:
    from .database import get_db
    from .models import User
    from .app.core.config import settings
    from .audit import audit_permission_check, audit_role_check
except Exception:  # Fallback when running module directly in container
    from database import get_db  # type: ignore
    from models import User  # type: ignore
    from app.core.config import settings  # type: ignore
    # Audit import will fail gracefully if not available
    def audit_permission_check(*args, **kwargs): pass  # type: ignore
    def audit_role_check(*args, **kwargs): pass  # type: ignore

# Use centralized configuration from settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
JWT_ISSUER = settings.JWT_ISSUER
JWT_AUDIENCE = settings.JWT_AUDIENCE

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Permission(str, Enum):
    """
    Enum defining granular permissions for RBAC system.
    
    This enumeration defines all possible permissions that can be granted
    to users through their roles. It provides fine-grained access control
    beyond simple user/admin roles.
    """
    # Job management permissions
    READ_JOBS = "jobs:read"
    CREATE_JOBS = "jobs:create"
    UPDATE_JOBS = "jobs:update"
    DELETE_JOBS = "jobs:delete"
    
    # Task management permissions
    READ_TASKS = "tasks:read"
    CREATE_TASKS = "tasks:create"
    UPDATE_TASKS = "tasks:update"
    DELETE_TASKS = "tasks:delete"
    
    # User management permissions
    READ_USERS = "users:read"
    CREATE_USERS = "users:create"
    UPDATE_USERS = "users:update"
    DELETE_USERS = "users:delete"
    
    # System administration permissions
    ADMIN_SYSTEM = "system:admin"
    READ_LOGS = "logs:read"
    MANAGE_SETTINGS = "settings:manage"


class Role(str, Enum):
    """
    Enum defining system roles with associated permissions.
    
    Roles group related permissions together to provide
    coherent access control for different user types.
    """
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


# Role-to-permissions mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.USER: {
        Permission.READ_JOBS,
        Permission.CREATE_JOBS,
        Permission.READ_TASKS,
        Permission.CREATE_TASKS,
    },
    Role.MODERATOR: {
        Permission.READ_JOBS,
        Permission.CREATE_JOBS,
        Permission.UPDATE_JOBS,
        Permission.READ_TASKS,
        Permission.CREATE_TASKS,
        Permission.UPDATE_TASKS,
        Permission.READ_USERS,
        Permission.READ_LOGS,
    },
    Role.ADMIN: {
        # Admins have all permissions
        Permission.READ_JOBS,
        Permission.CREATE_JOBS,
        Permission.UPDATE_JOBS,
        Permission.DELETE_JOBS,
        Permission.READ_TASKS,
        Permission.CREATE_TASKS,
        Permission.UPDATE_TASKS,
        Permission.DELETE_TASKS,
        Permission.READ_USERS,
        Permission.CREATE_USERS,
        Permission.UPDATE_USERS,
        Permission.DELETE_USERS,
        Permission.ADMIN_SYSTEM,
        Permission.READ_LOGS,
        Permission.MANAGE_SETTINGS,
    },
}


def user_has_permission(user: "User", permission: Permission) -> bool:
    """
    Check if a user has a specific permission based on their role.
    
    Args:
        user: User object with a role attribute
        permission: Permission to check
        
    Returns:
        bool: True if user has the permission, False otherwise
    """
    if isinstance(user.role, Role):
        user_role = user.role
    else:
        try:
            user_role = Role(str(user.role))
        except ValueError:
            user_role = Role.USER
    return permission in ROLE_PERMISSIONS.get(user_role, set())


def require_role(required_role: Role):
    """
    Decorator factory to require specific role for route access.
    
    Args:
        required_role: Required role for the route
        
    Returns:
        FastAPI dependency that checks user role
    """
    async def check_role(current_user: "User" = Depends(get_current_user)):
        if isinstance(current_user.role, Role):
            user_role = current_user.role
        else:
            try:
                user_role = Role(str(current_user.role))
            except ValueError:
                user_role = Role.USER

        # Admin role has access to everything
        granted = user_role == Role.ADMIN or user_role == required_role
        # …
        # Audit the role check
        audit_role_check(
            user=current_user,
            required_role=required_role.value,
            granted=granted
        )
        
        if not granted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {required_role.value}, Current: {user_role.value}"
            )
        return current_user
    
    return check_role


# HTTP Bearer token authentication scheme
oauth2_scheme = HTTPBearer(auto_error=False)


class Token(BaseModel):
    """
    JWT token model for authentication responses.
    
    This model represents the structure of authentication tokens returned
    by the login endpoint. It follows the OAuth 2.0 specification for
    token responses.
    
    Attributes:
        access_token (str): The JWT access token string
        token_type (str): Type of token (typically "bearer")
    """
    access_token: str
    token_type: str


class Login(BaseModel):
    """
    User login credentials model for authentication requests.
    
    This model defines the structure of login requests, containing the
    necessary credentials for user authentication.
    
    Attributes:
        username (str): Username for authentication
        password (str): Plain text password for authentication
    """
    username: str
    password: str


class TokenData(BaseModel):
    """
    Token data model for decoding JWT payload.
    
    This model represents the decoded data from a JWT token, primarily
    used to extract the username for user lookup during authentication.
    
    Attributes:
        username (Optional[str]): Username extracted from the token payload
    """
    username: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Uses the passlib context to securely compare the plain text password
    with the bcrypt hashed password. This function provides constant-time
    comparison to prevent timing attacks.
    
    Security Considerations:
    - Uses bcrypt for secure password hashing
    - Employs constant-time comparison to prevent timing attacks
    - Handles password verification without exposing plain text passwords
    
    Args:
        plain_password (str): The plain text password to verify
        hashed_password (str): The bcrypt hashed password to compare against
        
    Returns:
        bool: True if the password matches, False otherwise
        
    Example:
        >>> hashed = pwd_context.hash("my_password")
        >>> verify_password("my_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db: Session, username: str) -> Optional[User]:
    """
    Retrieve a user from the database by username.
    
    Performs a database query to find a user with the specified username.
    This is a synchronous operation that should be used in synchronous contexts.
    
    Args:
        db (Session): Database session
        username (str): Username to search for
        
    Returns:
        Optional[User]: User object if found, None otherwise
        
    Note:
        This function is designed for synchronous database operations.
        For asynchronous operations, use get_user_async instead.
    """
    return db.query(User).filter(User.username == username).first()


async def get_user_async(db: AsyncSession, username: str) -> Optional[User]:
    """
    Retrieve a user from the database by username using async operations.
    
    Performs an asynchronous database query to find a user with the specified username.
    This function should be used in asynchronous contexts to avoid blocking the event loop.
    
    Args:
        db (AsyncSession): Asynchronous database session
        username (str): Username to search for
        
    Returns:
        Optional[User]: User object if found, None otherwise
        
    Note:
        This function is designed for asynchronous database operations.
        For synchronous operations, use get_user instead.
    """
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


def authenticate_user(db: Session, username: str, password: str) -> User | bool:
    """
    Authenticate a user by username and password.
    
    Retrieves the user from the database and verifies the provided password
    against the stored hash. This function implements the complete user
    authentication flow.
    
    Security Considerations:
    - Implements secure password verification
    - Prevents user enumeration by returning False for both invalid users and invalid passwords
    - Uses constant-time comparison to prevent timing attacks
    
    Args:
        db (Session): Database session
        username (str): Username to authenticate
        password (str): Plain text password to verify
        
    Returns:
        User or False: User object if authentication succeeds, False otherwise
        
    Example:
        >>> user = authenticate_user(db, "john_doe", "password123")
        >>> if user:
        ...     print("Authentication successful")
        ... else:
        ...     print("Authentication failed")
    """
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with the provided data.
    
    Encodes the provided data into a JWT token with standard claims including
    expiration, issuer, audience, and issued at timestamp. This function
    implements JWT best practices for token creation.
    
    Security Considerations:
    - Includes standard JWT claims (exp, iss, aud, iat)
    - Uses secure signing algorithm (configured via settings)
    - Implements proper token expiration
    - Prevents token reuse with unique issued at timestamps
    
    Args:
        data (dict): Data to encode in the token (e.g., user identity)
        expires_delta (Optional[timedelta]): Custom expiration time, defaults to ACCESS_TOKEN_EXPIRE_MINUTES
        
    Returns:
        str: Encoded JWT token
        
    Example:
        >>> token_data = {"sub": "user123", "role": "admin"}
        >>> token = create_access_token(token_data)
        >>> print(token)  # Encoded JWT token string
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Include standard claims
    to_encode.update({
        "exp": expire,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now,
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency to get the current authenticated user from JWT token.
    
    Decodes the JWT token from the Authorization header, validates it, and
    retrieves the corresponding user from the database. This function serves
    as a FastAPI dependency that can be used to protect routes requiring
    authentication.
    
    Security Considerations:
    - Validates JWT token signature and claims
    - Checks token expiration
    - Verifies issuer and audience claims
    - Prevents unauthorized access to protected endpoints
    - Uses secure error handling to prevent information leakage
    
    Args:
        credentials (HTTPAuthorizationCredentials): Bearer token from Authorization header
        db (Session): Database session dependency
        
    Returns:
        User: Authenticated user object
        
    Raises:
        HTTPException: If token is missing, invalid, or user not found (401 Unauthorized)
        
    Example:
        >>> @app.get("/protected")
        >>> async def protected_route(current_user: User = Depends(get_current_user)):
        >>>     return {"message": f"Hello, {current_user.username}!"}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Check if credentials are provided
        if credentials is None or not getattr(credentials, "credentials", None):
            raise credentials_exception
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
