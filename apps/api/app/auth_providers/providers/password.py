"""Password-based authentication provider."""

from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from . import AuthProvider
from ...db.models import User

# Import from auth.py module (separate from auth package)
import app.auth as auth_module


class PasswordAuthProvider(AuthProvider):
    """
    Email/password authentication provider.
    
    Uses bcrypt for password hashing and verification.
    """
    
    async def authenticate(self, credentials: dict, **kwargs) -> User:
        """
        Authenticate user with email and password.
        
        Args:
            credentials: Dict with 'email' and 'password' keys
            **kwargs: Must include 'session' (AsyncSession)
            
        Returns:
            Authenticated User object
            
        Raises:
            HTTPException: 401 if credentials invalid
        """
        session: AsyncSession = kwargs.get('session')
        if not session:
            raise ValueError("PasswordAuthProvider requires 'session' in kwargs")
        
        email = credentials.get('email')
        password = credentials.get('password')
        
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password required"
            )
        
        # Use existing authenticate_user function
        user = await auth_module.authenticate_user(session, email, password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    async def link_account(self, user_id: str, credentials: Any, **kwargs) -> bool:
        """
        Password auth doesn't support account linking.
        
        Returns:
            False (password auth is primary method)
        """
        return False
    
    def get_login_url(self, state: str, redirect_uri: str) -> None:
        """Password auth doesn't use redirects."""
        return None
    
    def requires_redirect(self) -> bool:
        """Password auth doesn't require redirects."""
        return False
