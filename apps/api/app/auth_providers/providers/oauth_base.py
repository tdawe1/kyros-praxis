"""
Base OAuth provider implementation.

TEMPLATE for future OAuth providers (Google, GitHub, etc.)
Implement this when adding OAuth support.
"""

from typing import Any, Optional
from abc import abstractmethod

from . import AuthProvider
from ...db.models import User


class OAuthProvider(AuthProvider):
    """
    Base class for OAuth 2.0 providers.
    
    Subclass this to implement specific providers:
    - GoogleOAuthProvider
    - GitHubOAuthProvider
    - AzureADOAuthProvider
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorize_url: str,
        token_url: str,
        userinfo_url: str,
        scopes: list[str]
    ):
        """
        Initialize OAuth provider.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            authorize_url: Provider's authorization endpoint
            token_url: Provider's token endpoint
            userinfo_url: Provider's user info endpoint
            scopes: OAuth scopes to request
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.userinfo_url = userinfo_url
        self.scopes = scopes
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider identifier (e.g., 'google', 'github')."""
        pass
    
    def get_login_url(self, state: str, redirect_uri: str) -> str:
        """
        Generate OAuth authorization URL.
        
        Args:
            state: CSRF protection state token
            redirect_uri: Callback URL
            
        Returns:
            OAuth authorization URL
        """
        from urllib.parse import urlencode
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.scopes),
            'state': state,
        }
        
        return f"{self.authorize_url}?{urlencode(params)}"
    
    def requires_redirect(self) -> bool:
        """OAuth requires redirect flow."""
        return True
    
    async def authenticate(self, credentials: dict, **kwargs) -> User:
        """
        Authenticate user via OAuth.
        
        Args:
            credentials: Dict with 'code' (authorization code)
            **kwargs: Must include 'session' (AsyncSession)
            
        Returns:
            Authenticated User object
        """
        # TEMPLATE - Implement when adding OAuth
        raise NotImplementedError(
            f"OAuth authentication not yet implemented. "
            f"To add OAuth support, implement {self.__class__.__name__}.authenticate()"
        )
    
    async def link_account(self, user_id: str, credentials: Any, **kwargs) -> bool:
        """
        Link OAuth account to existing user.
        
        Args:
            user_id: Existing user ID
            credentials: OAuth credentials
            **kwargs: Additional context
            
        Returns:
            True if linked successfully
        """
        # TEMPLATE - Implement when adding OAuth
        raise NotImplementedError(
            f"OAuth account linking not yet implemented. "
            f"To add OAuth support, implement {self.__class__.__name__}.link_account()"
        )


# Template OAuth provider implementations
# Uncomment and complete when implementing OAuth

# class GoogleOAuthProvider(OAuthProvider):
#     """Google OAuth 2.0 provider."""
#     
#     def __init__(self, client_id: str, client_secret: str):
#         super().__init__(
#             client_id=client_id,
#             client_secret=client_secret,
#             authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
#             token_url="https://oauth2.googleapis.com/token",
#             userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
#             scopes=["openid", "email", "profile"]
#         )
#     
#     def get_provider_name(self) -> str:
#         return "google"


# class GitHubOAuthProvider(OAuthProvider):
#     """GitHub OAuth 2.0 provider."""
#     
#     def __init__(self, client_id: str, client_secret: str):
#         super().__init__(
#             client_id=client_id,
#             client_secret=client_secret,
#             authorize_url="https://github.com/login/oauth/authorize",
#             token_url="https://github.com/login/oauth/access_token",
#             userinfo_url="https://api.github.com/user",
#             scopes=["user:email"]
#         )
#     
#     def get_provider_name(self) -> str:
#         return "github"
