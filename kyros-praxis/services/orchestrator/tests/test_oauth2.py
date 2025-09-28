"""
Tests for OAuth2 authentication functionality.

This module contains comprehensive tests for the OAuth2 authentication system,
including provider configuration, authorization flows, token management, and
refresh token functionality.
"""

import pytest
import os
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.orchestrator.oauth2 import OAuth2Manager, OAuth2Config, RefreshTokenRequest
from services.orchestrator.models import Base, User, RefreshToken, OAuthProvider, UserOAuth
from services.orchestrator.database import get_db
from services.orchestrator.main import app
from services.orchestrator.auth import pwd_context

# Set environment variables for testing
os.environ["SECRET_KEY"] = "test-secret-key-for-oauth2-testing"
os.environ["ENVIRONMENT"] = "local"


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db

    yield TestingSessionLocal()

    # Clean up
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create a test client with test database."""
    return TestClient(app)


@pytest.fixture
def oauth2_manager():
    """Create an OAuth2Manager instance for testing."""
    return OAuth2Manager()


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = User(
        username="testuser@example.com",
        email="testuser@example.com",
        password_hash=pwd_context.hash("password123"),
        role="user",
        active=1
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def google_provider(test_db):
    """Create a Google OAuth2 provider configuration."""
    provider = OAuthProvider(
        name="google",
        client_id="test_google_client_id",
        client_secret="test_google_client_secret",
        authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        user_info_url="https://www.googleapis.com/oauth2/v2/userinfo",
        scopes=["openid", "email", "profile"],
        active=1
    )
    test_db.add(provider)
    test_db.commit()
    test_db.refresh(provider)
    return provider


class TestOAuth2Manager:
    """Test OAuth2Manager functionality."""
    
    def test_hash_token(self, oauth2_manager):
        """Test token hashing."""
        token = "test_token_123"
        hash1 = oauth2_manager.hash_token(token)
        hash2 = oauth2_manager.hash_token(token)
        
        assert hash1 == hash2  # Same token produces same hash
        assert hash1 != token  # Hash is different from original token
        assert len(hash1) == 64  # SHA256 produces 64-character hex string
    
    def test_generate_state(self, oauth2_manager):
        """Test state parameter generation."""
        state1 = oauth2_manager.generate_state()
        state2 = oauth2_manager.generate_state()
        
        assert state1 != state2  # Different states
        assert len(state1) >= 32  # Sufficiently long
        assert state1.replace('-', '').replace('_', '').isalnum()  # URL-safe
    
    def test_generate_pkce_challenge(self, oauth2_manager):
        """Test PKCE challenge generation."""
        verifier, challenge = oauth2_manager.generate_pkce_challenge()
        
        assert verifier != challenge
        assert len(verifier) >= 32
        assert len(challenge) >= 32
        # Verify both are URL-safe
        assert verifier.replace('-', '').replace('_', '').isalnum()
        assert challenge.replace('-', '').replace('_', '').isalnum()
    
    @pytest.mark.asyncio
    async def test_get_provider_config(self, oauth2_manager, test_db, google_provider):
        """Test getting provider configuration."""
        config = await oauth2_manager.get_provider_config(test_db, "google")
        
        assert config is not None
        assert config.name == "google"
        assert config.client_id == "test_google_client_id"
        assert config.authorization_url == "https://accounts.google.com/o/oauth2/v2/auth"
        assert "openid" in config.scopes
    
    @pytest.mark.asyncio
    async def test_get_provider_config_not_found(self, oauth2_manager, test_db):
        """Test getting non-existent provider configuration."""
        config = await oauth2_manager.get_provider_config(test_db, "nonexistent")
        assert config is None
    
    @pytest.mark.asyncio
    async def test_create_or_update_provider(self, oauth2_manager, test_db):
        """Test creating and updating provider configuration."""
        config = OAuth2Config(
            name="github",
            client_id="test_github_client_id",
            client_secret="test_github_client_secret",
            authorization_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            user_info_url="https://api.github.com/user",
            scopes=["user:email"]
        )
        
        # Create provider
        provider = await oauth2_manager.create_or_update_provider(test_db, config)
        assert provider.name == "github"
        assert provider.client_id == "test_github_client_id"
        
        # Update provider
        config.client_id = "updated_github_client_id"
        updated_provider = await oauth2_manager.create_or_update_provider(test_db, config)
        assert updated_provider.id == provider.id
        assert updated_provider.client_id == "updated_github_client_id"
    
    @pytest.mark.asyncio
    async def test_get_authorization_url(self, oauth2_manager, test_db, google_provider):
        """Test authorization URL generation."""
        redirect_uri = "http://localhost:8000/auth/callback"
        auth_url, state = await oauth2_manager.get_authorization_url(
            test_db, "google", redirect_uri
        )
        
        assert "accounts.google.com" in auth_url
        assert "client_id=test_google_client_id" in auth_url
        assert "redirect_uri=" in auth_url
        assert "code_challenge=" in auth_url
        assert "state=" in auth_url
        assert len(state) > 32  # State includes code_verifier
    
    @pytest.mark.asyncio
    async def test_create_refresh_token(self, oauth2_manager, test_db, test_user):
        """Test refresh token creation."""
        refresh_token = await oauth2_manager.create_refresh_token(test_db, test_user.id)
        
        assert refresh_token.user_id == test_user.id
        assert refresh_token.token_hash is not None
        assert refresh_token.token_family is not None
        assert refresh_token.expires_at > datetime.now()  # Remove timezone.utc
        assert hasattr(refresh_token, 'raw_token')
        assert len(refresh_token.raw_token) > 32
    
    @pytest.mark.asyncio
    async def test_refresh_access_token(self, oauth2_manager, test_db, test_user):
        """Test access token refresh."""
        # Create initial refresh token
        refresh_token = await oauth2_manager.create_refresh_token(test_db, test_user.id)
        raw_token = refresh_token.raw_token
        
        # Refresh the access token
        tokens = await oauth2_manager.refresh_access_token(test_db, raw_token)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "expires_in" in tokens
        assert tokens["token_type"] == "bearer"
        
        # Original refresh token should be marked as used
        db_token = test_db.query(RefreshToken).filter(
            RefreshToken.id == refresh_token.id
        ).first()
        assert db_token.used_at is not None
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid(self, oauth2_manager, test_db):
        """Test access token refresh with invalid token."""
        with pytest.raises(Exception):  # Should raise HTTPException
            await oauth2_manager.refresh_access_token(test_db, "invalid_token")
    
    @pytest.mark.asyncio
    async def test_revoke_refresh_token(self, oauth2_manager, test_db, test_user):
        """Test refresh token revocation."""
        # Create refresh token
        refresh_token = await oauth2_manager.create_refresh_token(test_db, test_user.id)
        raw_token = refresh_token.raw_token
        
        # Revoke token
        success = await oauth2_manager.revoke_refresh_token(test_db, raw_token)
        assert success is True
        
        # Token should be marked as revoked
        db_token = test_db.query(RefreshToken).filter(
            RefreshToken.id == refresh_token.id
        ).first()
        assert db_token.revoked_at is not None
    
    @pytest.mark.asyncio
    async def test_revoke_token_family(self, oauth2_manager, test_db, test_user):
        """Test revoking all tokens in a family."""
        # Create multiple tokens in the same family
        token1 = await oauth2_manager.create_refresh_token(test_db, test_user.id)
        token_family = token1.token_family
        token2 = await oauth2_manager.create_refresh_token(test_db, test_user.id, token_family)
        
        # Revoke family
        count = await oauth2_manager.revoke_token_family(test_db, token_family)
        assert count == 2
        
        # Both tokens should be revoked
        db_tokens = test_db.query(RefreshToken).filter(
            RefreshToken.token_family == token_family
        ).all()
        for token in db_tokens:
            assert token.revoked_at is not None
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self, oauth2_manager, test_db, test_user):
        """Test cleanup of expired tokens."""
        # Create an expired token
        expired_token = RefreshToken(
            user_id=test_user.id,
            token_hash="expired_hash",
            token_family="expired_family",
            expires_at=datetime.now() - timedelta(days=1)  # Remove timezone.utc
        )
        test_db.add(expired_token)
        test_db.commit()
        
        # Cleanup expired tokens
        count = await oauth2_manager.cleanup_expired_tokens(test_db)
        assert count == 1
        
        # Token should be deleted
        db_token = test_db.query(RefreshToken).filter(
            RefreshToken.id == expired_token.id
        ).first()
        assert db_token is None


class TestOAuth2Endpoints:
    """Test OAuth2 API endpoints."""
    
    def test_refresh_token_endpoint(self, client, test_db, test_user):
        """Test the token refresh endpoint."""
        # Create a refresh token
        oauth2_manager = OAuth2Manager()
        refresh_token = test_db.execute(
            text("SELECT token_hash FROM refresh_tokens WHERE user_id = :user_id"),
            {"user_id": test_user.id}
        ).first()
        
        if not refresh_token:
            # Create a refresh token for testing
            from services.orchestrator.oauth2 import OAuth2Manager
            import asyncio
            
            async def create_token():
                manager = OAuth2Manager()
                return await manager.create_refresh_token(test_db, test_user.id)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                refresh_token_obj = loop.run_until_complete(create_token())
                raw_token = refresh_token_obj.raw_token
            finally:
                loop.close()
        
            response = client.post(
                "/auth/refresh",
                json={"refresh_token": raw_token}
            )
            
            # Should return 200 with new tokens
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
    
    def test_oauth2_authorize_endpoint(self, client, test_db, google_provider):
        """Test OAuth2 authorization endpoint."""
        response = client.get(
            "/auth/oauth2/google",
            params={"redirect_uri": "http://localhost:8000/callback"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "state" in data
        assert "accounts.google.com" in data["authorization_url"]
    
    def test_oauth2_authorize_invalid_provider(self, client, test_db):
        """Test OAuth2 authorization with invalid provider."""
        response = client.get(
            "/auth/oauth2/invalid_provider",
            params={"redirect_uri": "http://localhost:8000/callback"}
        )
        
        assert response.status_code == 404
    
    @patch('httpx.AsyncClient.post')
    @patch('httpx.AsyncClient.get')
    def test_oauth2_callback_endpoint(self, mock_get, mock_post, client, test_db, google_provider):
        """Test OAuth2 callback endpoint."""
        # Mock token exchange response
        mock_post.return_value.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "bearer",
            "expires_in": 3600,
            "refresh_token": "test_refresh_token"
        }
        mock_post.return_value.raise_for_status = MagicMock()
        
        # Mock user info response
        mock_get.return_value.json.return_value = {
            "id": "12345",
            "email": "newuser@example.com",
            "name": "New User"
        }
        mock_get.return_value.raise_for_status = MagicMock()
        
        response = client.post(
            "/auth/oauth2/google/callback",
            params={
                "code": "test_auth_code",
                "state": "test_state:test_verifier",
                "redirect_uri": "http://localhost:8000/callback"
            }
        )
        
        # Should create user and return tokens
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
    
    def test_get_user_profile_endpoint(self, client, test_db, test_user):
        """Test user profile endpoint."""
        # Create access token
        from services.orchestrator.auth import create_access_token
        access_token = create_access_token(data={"sub": test_user.username})
        
        response = client.get(
            "/auth/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert data["role"] == test_user.role
    
    def test_logout_endpoint(self, client, test_db, test_user):
        """Test logout endpoint."""
        # Create access token and refresh token
        from services.orchestrator.auth import create_access_token
        access_token = create_access_token(data={"sub": test_user.username})
        
        # Create refresh token for testing
        import asyncio
        from services.orchestrator.oauth2 import OAuth2Manager
        
        async def create_token():
            manager = OAuth2Manager()
            return await manager.create_refresh_token(test_db, test_user.id)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            refresh_token_obj = loop.run_until_complete(create_token())
            raw_token = refresh_token_obj.raw_token
        finally:
            loop.close()
        
        response = client.post(
            "/auth/logout",
            json={"refresh_token": raw_token},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["token_revoked"] is True


class TestRefreshTokenModel:
    """Test RefreshToken model functionality."""
    
    def test_refresh_token_creation(self, test_db, test_user):
        """Test creating a refresh token."""
        token = RefreshToken(
            user_id=test_user.id,
            token_hash="test_hash",
            token_family="test_family",
            expires_at=datetime.now() + timedelta(days=30)
        )
        test_db.add(token)
        test_db.commit()
        test_db.refresh(token)
        
        assert token.id is not None
        assert token.user_id == test_user.id
        assert token.expires_at > datetime.now()
        assert token.created_at is not None
        assert token.used_at is None
        assert token.revoked_at is None
    
    def test_refresh_token_relationship(self, test_db, test_user):
        """Test refresh token relationship with user."""
        token = RefreshToken(
            user_id=test_user.id,
            token_hash="test_hash",
            token_family="test_family",
            expires_at=datetime.now() + timedelta(days=30)
        )
        test_db.add(token)
        test_db.commit()
        
        # Test relationship
        assert token.user.id == test_user.id
        assert len(test_user.refresh_tokens) == 1
        assert test_user.refresh_tokens[0].id == token.id


class TestOAuthProviderModel:
    """Test OAuthProvider model functionality."""
    
    def test_oauth_provider_creation(self, test_db):
        """Test creating an OAuth provider."""
        provider = OAuthProvider(
            name="test_provider",
            client_id="test_client_id",
            client_secret="test_client_secret",
            authorization_url="https://example.com/auth",
            token_url="https://example.com/token",
            user_info_url="https://example.com/userinfo",
            scopes=["scope1", "scope2"],
            active=1
        )
        test_db.add(provider)
        test_db.commit()
        test_db.refresh(provider)
        
        assert provider.id is not None
        assert provider.name == "test_provider"
        assert provider.scopes == ["scope1", "scope2"]
        assert provider.active == 1
        assert provider.created_at is not None


class TestUserOAuthModel:
    """Test UserOAuth model functionality."""
    
    def test_user_oauth_creation(self, test_db, test_user):
        """Test creating a user OAuth link."""
        oauth_link = UserOAuth(
            user_id=test_user.id,
            provider_name="google",
            provider_user_id="12345",
            provider_username="testuser",
            provider_email="testuser@gmail.com",
            access_token_hash="access_token_hash",
            refresh_token_hash="refresh_token_hash"
        )
        test_db.add(oauth_link)
        test_db.commit()
        test_db.refresh(oauth_link)
        
        assert oauth_link.id is not None
        assert oauth_link.user_id == test_user.id
        assert oauth_link.provider_name == "google"
        assert oauth_link.created_at is not None
        assert oauth_link.updated_at is not None
    
    def test_user_oauth_relationship(self, test_db, test_user):
        """Test user OAuth relationship."""
        oauth_link = UserOAuth(
            user_id=test_user.id,
            provider_name="google",
            provider_user_id="12345",
            provider_username="testuser",
            provider_email="testuser@gmail.com"
        )
        test_db.add(oauth_link)
        test_db.commit()
        
        # Test relationship
        assert oauth_link.user.id == test_user.id
        assert len(test_user.oauth_accounts) == 1
        assert test_user.oauth_accounts[0].id == oauth_link.id