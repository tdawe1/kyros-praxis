"""
Authentication provider abstraction.

Supports multiple authentication methods (password, OAuth, etc.)
and makes it easy to add new providers in the future.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from ...db.models import User


class AuthProvider(ABC):
    """
    Base authentication provider interface.
    
    All authentication methods (password, OAuth, SAML, etc.) implement this interface.
    """
    
    @abstractmethod
    async def authenticate(self, credentials: Any, **kwargs) -> User:
        """
        Authenticate user with provided credentials.
        
        Args:
            credentials: Provider-specific credentials
            **kwargs: Additional context (session, request, etc.)
            
        Returns:
            Authenticated User object
            
        Raises:
            HTTPException: If authentication fails
        """
        pass
    
    @abstractmethod
    async def link_account(self, user_id: str, credentials: Any, **kwargs) -> bool:
        """
        Link external account to existing user.
        
        Args:
            user_id: Existing user ID
            credentials: Provider-specific credentials
            **kwargs: Additional context
            
        Returns:
            True if linked successfully, False otherwise
        """
        pass
    
    def get_login_url(self, state: str, redirect_uri: str) -> Optional[str]:
        """
        Get OAuth login URL (None for non-OAuth providers).
        
        Args:
            state: CSRF protection state token
            redirect_uri: Where to redirect after auth
            
        Returns:
            OAuth login URL or None
        """
        return None
    
    def requires_redirect(self) -> bool:
        """Check if this provider requires OAuth redirect flow."""
        return False


__all__ = ["AuthProvider"]
