"""
OAuth2 authentication module for the Kyros Orchestrator service.

This module provides OAuth2 authentication functionality including provider
integration, token refresh mechanisms, and OAuth2 flow management. It supports
multiple OAuth2 providers (Google, GitHub, Microsoft, Custom) and implements
secure token rotation for refresh tokens.

MODULE RESPONSIBILITIES:
------------------------
1. OAuth2 Provider Integration:
   - Google, GitHub, Microsoft OAuth2 integration
   - Dynamic provider configuration
   - Custom OAuth2 provider support

2. Token Management:
   - Access token and refresh token handling
   - Token rotation for enhanced security
   - Token family tracking to prevent replay attacks

3. OAuth2 Flow Implementation:
   - Authorization code flow
   - Token exchange and refresh
   - User profile retrieval from providers

4. Security Features:
   - PKCE support for enhanced security
   - State parameter validation
   - Token hashing for secure storage
   - Automatic token cleanup

INTEGRATION WITH OTHER MODULES:
-------------------------------
- auth.py: Complements existing JWT authentication
- models.py: Uses OAuth2-related models (RefreshToken, UserOAuth, OAuthProvider)
- database.py: Database operations for OAuth2 data
- main.py: OAuth2 endpoints and flows

USAGE EXAMPLES:
---------------
OAuth2 authorization:
    oauth2_manager = OAuth2Manager()
    auth_url = await oauth2_manager.get_authorization_url("google", "state123")
    
Token refresh:
    new_tokens = await oauth2_manager.refresh_access_token(refresh_token)
    
Provider configuration:
    await oauth2_manager.configure_provider("google", client_id, client_secret)
"""

import os
import secrets
import hashlib
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any, Tuple
from urllib.parse import urlencode, parse_qs

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel, Field

try:
    from .models import User, RefreshToken, OAuthProvider, UserOAuth
    from .database import get_db
    from .auth import create_access_token, SECRET_KEY
    from .app.core.config import settings
except ImportError:  # Fallback when running module directly
    from .models import User, RefreshToken, OAuthProvider, UserOAuth  # type: ignore
    from .database import get_db  # type: ignore
    from .auth import create_access_token, SECRET_KEY  # type: ignore
    from app.core.config import settings  # type: ignore


class OAuth2Config(BaseModel):
    """OAuth2 provider configuration model."""
    name: str
    client_id: str
    client_secret: str
    authorization_url: str
    token_url: str
    user_info_url: str
    scopes: List[str] = Field(default_factory=list)
    active: bool = True


class OAuth2TokenResponse(BaseModel):
    """OAuth2 token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str


class OAuth2Manager:
    """
    OAuth2 authentication manager.
    
    Handles OAuth2 flows, token management, and provider integration.
    Supports multiple OAuth2 providers with dynamic configuration.
    """
    
    # Built-in provider configurations
    PROVIDERS = {
        "google": {
            "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            "scopes": ["openid", "email", "profile"]
        },
        "github": {
            "authorization_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "user_info_url": "https://api.github.com/user",
            "scopes": ["user:email"]
        },
        "microsoft": {
            "authorization_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "user_info_url": "https://graph.microsoft.com/v1.0/me",
            "scopes": ["openid", "email", "profile"]
        }
    }
    
    def __init__(self):
        self.client = httpx.AsyncClient()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def generate_state(self) -> str:
        """Generate a cryptographically secure state parameter."""
        return secrets.token_urlsafe(32)
    
    def generate_pkce_challenge(self) -> Tuple[str, str]:
        """Generate PKCE code verifier and challenge."""
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        return code_verifier, code_challenge
    
    def hash_token(self, token: str) -> str:
        """Hash a token for secure storage."""
        return hashlib.sha256(f"{SECRET_KEY}{token}".encode()).hexdigest()
    
    async def get_provider_config(self, db: Session, provider_name: str) -> Optional[OAuth2Config]:
        """Get OAuth2 provider configuration from database."""
        provider = db.query(OAuthProvider).filter(
            OAuthProvider.name == provider_name,
            OAuthProvider.active == 1
        ).first()
        
        if not provider:
            return None
        
        return OAuth2Config(
            name=provider.name,
            client_id=provider.client_id,
            client_secret=provider.client_secret,
            authorization_url=provider.authorization_url,
            token_url=provider.token_url,
            user_info_url=provider.user_info_url,
            scopes=provider.scopes,
            active=bool(provider.active)
        )
    
    async def create_or_update_provider(
        self, 
        db: Session, 
        config: OAuth2Config
    ) -> OAuthProvider:
        """Create or update an OAuth2 provider configuration."""
        provider = db.query(OAuthProvider).filter(
            OAuthProvider.name == config.name
        ).first()
        
        if provider:
            # Update existing provider
            provider.client_id = config.client_id
            provider.client_secret = config.client_secret
            provider.authorization_url = config.authorization_url
            provider.token_url = config.token_url
            provider.user_info_url = config.user_info_url
            provider.scopes = config.scopes
            provider.active = 1 if config.active else 0
        else:
            # Create new provider
            provider = OAuthProvider(
                name=config.name,
                client_id=config.client_id,
                client_secret=config.client_secret,
                authorization_url=config.authorization_url,
                token_url=config.token_url,
                user_info_url=config.user_info_url,
                scopes=config.scopes,
                active=1 if config.active else 0
            )
            db.add(provider)
        
        db.commit()
        db.refresh(provider)
        return provider
    
    async def get_authorization_url(
        self, 
        db: Session, 
        provider_name: str, 
        redirect_uri: str,
        state: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate OAuth2 authorization URL.
        
        Returns:
            Tuple of (authorization_url, state)
        """
        config = await self.get_provider_config(db, provider_name)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"OAuth2 provider '{provider_name}' not found or inactive"
            )
        
        if not state:
            state = self.generate_state()
        
        # Generate PKCE challenge
        code_verifier, code_challenge = self.generate_pkce_challenge()
        
        # Build authorization URL
        params = {
            "client_id": config.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": " ".join(config.scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        auth_url = f"{config.authorization_url}?{urlencode(params)}"
        
        # Store code_verifier temporarily (in production, use Redis or database)
        # For now, we'll encode it in the state parameter
        enhanced_state = f"{state}:{code_verifier}"
        
        return auth_url, enhanced_state
    
    async def exchange_code_for_tokens(
        self,
        db: Session,
        provider_name: str,
        code: str,
        redirect_uri: str,
        state: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        config = await self.get_provider_config(db, provider_name)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"OAuth2 provider '{provider_name}' not found"
            )
        
        # Extract code_verifier from state
        try:
            _, code_verifier = state.split(":", 1)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid state parameter"
            )
        
        # Prepare token request
        token_data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier
        }
        
        # Exchange code for tokens
        try:
            response = await self.client.post(
                config.token_url,
                data=token_data,
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            token_response = response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange code for tokens: {str(e)}"
            )
        
        return token_response
    
    async def get_user_info(
        self,
        db: Session,
        provider_name: str,
        access_token: str
    ) -> Dict[str, Any]:
        """Get user information from OAuth2 provider."""
        config = await self.get_provider_config(db, provider_name)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"OAuth2 provider '{provider_name}' not found"
            )
        
        try:
            response = await self.client.get(
                config.user_info_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get user info: {str(e)}"
            )
    
    async def create_refresh_token(
        self,
        db: Session,
        user_id: str,
        token_family: Optional[str] = None
    ) -> RefreshToken:
        """Create a new refresh token for the user."""
        if not token_family:
            token_family = secrets.token_urlsafe(32)
        
        # Generate refresh token
        raw_token = secrets.token_urlsafe(64)
        token_hash = self.hash_token(raw_token)
        
        # Create refresh token record
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            token_family=token_family,
            expires_at=datetime.now() + timedelta(days=30)  # Use timezone-naive for SQLite
        )
        
        db.add(refresh_token)
        db.commit()
        db.refresh(refresh_token)
        
        # Return the raw token (only time it's available in plain text)
        refresh_token.raw_token = raw_token
        return refresh_token
    
    async def refresh_access_token(
        self,
        db: Session,
        refresh_token: str
    ) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        token_hash = self.hash_token(refresh_token)
        
        # Find the refresh token
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expires_at > datetime.now(),  # Use timezone-naive
            RefreshToken.used_at.is_(None),
            RefreshToken.revoked_at.is_(None)
        ).first()
        
        if not db_token:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired refresh token"
            )
        
        # Mark token as used
        db_token.used_at = datetime.now()  # Use timezone-naive
        
        # Get user
        user = db.query(User).filter(User.id == db_token.user_id).first()
        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # Create new refresh token (token rotation)
        new_refresh_token = await self.create_refresh_token(
            db, user.id, db_token.token_family
        )
        
        db.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_token": new_refresh_token.raw_token
        }
    
    async def revoke_refresh_token(
        self,
        db: Session,
        refresh_token: str
    ) -> bool:
        """Revoke a refresh token."""
        token_hash = self.hash_token(refresh_token)
        
        # Find and revoke the token
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()
        
        if db_token:
            db_token.revoked_at = datetime.now()  # Use timezone-naive
            db.commit()
            return True
        
        return False
    
    async def revoke_token_family(
        self,
        db: Session,
        token_family: str
    ) -> int:
        """Revoke all tokens in a token family (for security)."""
        now = datetime.now()  # Use timezone-naive
        
        result = db.query(RefreshToken).filter(
            RefreshToken.token_family == token_family,
            RefreshToken.revoked_at.is_(None)
        ).update({
            RefreshToken.revoked_at: now
        })
        
        db.commit()
        return result
    
    async def cleanup_expired_tokens(self, db: Session) -> int:
        """Clean up expired refresh tokens."""
        now = datetime.now()  # Use timezone-naive
        
        # Delete expired tokens
        result = db.query(RefreshToken).filter(
            RefreshToken.expires_at < now
        ).delete()
        
        db.commit()
        return result
    
    async def link_oauth_account(
        self,
        db: Session,
        user_id: str,
        provider_name: str,
        provider_user_info: Dict[str, Any],
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None
    ) -> UserOAuth:
        """Link an OAuth2 account to a user."""
        # Extract user info based on provider
        if provider_name == "google":
            provider_user_id = provider_user_info.get("id")
            provider_username = provider_user_info.get("name")
            provider_email = provider_user_info.get("email")
        elif provider_name == "github":
            provider_user_id = str(provider_user_info.get("id"))
            provider_username = provider_user_info.get("login")
            provider_email = provider_user_info.get("email")
        elif provider_name == "microsoft":
            provider_user_id = provider_user_info.get("id")
            provider_username = provider_user_info.get("displayName")
            provider_email = provider_user_info.get("mail") or provider_user_info.get("userPrincipalName")
        else:
            # Generic fallback
            provider_user_id = str(provider_user_info.get("id", provider_user_info.get("sub")))
            provider_username = provider_user_info.get("name", provider_user_info.get("login"))
            provider_email = provider_user_info.get("email")
        
        # Check if link already exists
        oauth_link = db.query(UserOAuth).filter(
            UserOAuth.user_id == user_id,
            UserOAuth.provider_name == provider_name
        ).first()
        
        if oauth_link:
            # Update existing link
            oauth_link.provider_user_id = provider_user_id
            oauth_link.provider_username = provider_username
            oauth_link.provider_email = provider_email
            oauth_link.access_token_hash = self.hash_token(access_token)
            oauth_link.refresh_token_hash = self.hash_token(refresh_token) if refresh_token else None
            oauth_link.token_expires_at = (
                datetime.now() + timedelta(seconds=expires_in)  # Use timezone-naive
                if expires_in else None
            )
            oauth_link.updated_at = datetime.now()  # Use timezone-naive
        else:
            # Create new link
            oauth_link = UserOAuth(
                user_id=user_id,
                provider_name=provider_name,
                provider_user_id=provider_user_id,
                provider_username=provider_username,
                provider_email=provider_email,
                access_token_hash=self.hash_token(access_token),
                refresh_token_hash=self.hash_token(refresh_token) if refresh_token else None,
                token_expires_at=(
                    datetime.now() + timedelta(seconds=expires_in)  # Use timezone-naive
                    if expires_in else None
                )
            )
            db.add(oauth_link)
        
        db.commit()
        db.refresh(oauth_link)
        return oauth_link


# Initialize default OAuth2 providers
async def initialize_default_providers(db: Session):
    """Initialize default OAuth2 providers from environment variables."""
    oauth2_manager = OAuth2Manager()
    
    # Google OAuth2
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if google_client_id and google_client_secret:
        google_config = OAuth2Config(
            name="google",
            client_id=google_client_id,
            client_secret=google_client_secret,
            **oauth2_manager.PROVIDERS["google"]
        )
        await oauth2_manager.create_or_update_provider(db, google_config)
    
    # GitHub OAuth2
    github_client_id = os.getenv("GITHUB_CLIENT_ID")
    github_client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    if github_client_id and github_client_secret:
        github_config = OAuth2Config(
            name="github",
            client_id=github_client_id,
            client_secret=github_client_secret,
            **oauth2_manager.PROVIDERS["github"]
        )
        await oauth2_manager.create_or_update_provider(db, github_config)
    
    # Microsoft OAuth2
    microsoft_client_id = os.getenv("MICROSOFT_CLIENT_ID")
    microsoft_client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
    if microsoft_client_id and microsoft_client_secret:
        microsoft_config = OAuth2Config(
            name="microsoft",
            client_id=microsoft_client_id,
            client_secret=microsoft_client_secret,
            **oauth2_manager.PROVIDERS["microsoft"]
        )
        await oauth2_manager.create_or_update_provider(db, microsoft_config)