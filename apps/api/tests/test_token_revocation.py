"""
Integration tests for token revocation system.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

# Test the token blacklist functionality
class TestTokenBlacklist:
    """Test token revocation via Redis blacklist."""
    
    @pytest.fixture
    def blacklist(self):
        """Create a token blacklist instance."""
        from app.auth_providers.token_blacklist import TokenBlacklist
        bl = TokenBlacklist()
        return bl
    
    @pytest.mark.asyncio
    async def test_revoke_token_memory_fallback(self, blacklist):
        """Test token revocation works with in-memory fallback."""
        # Without Redis, should use memory fallback
        result = await blacklist.revoke_token("test-jti-123", ttl_seconds=60)
        assert result is True
        
        # Check if revoked
        is_revoked = await blacklist.is_revoked("test-jti-123")
        assert is_revoked is True
    
    @pytest.mark.asyncio
    async def test_non_revoked_token(self, blacklist):
        """Test non-revoked token returns False."""
        is_revoked = await blacklist.is_revoked("never-revoked-jti")
        assert is_revoked is False
    
    @pytest.mark.asyncio
    async def test_revoke_all_for_user(self, blacklist):
        """Test revoking all tokens for a user."""
        result = await blacklist.revoke_all_for_user("user-123")
        assert result is True


class TestTokenTypeEnforcement:
    """Test that refresh tokens cannot be used for API access."""
    
    @pytest.mark.asyncio
    async def test_access_token_accepted(self):
        """Access tokens should be accepted for API endpoints."""
        from app.auth import create_access_token
        
        token = create_access_token({"sub": "test@example.com"})
        assert token is not None
        assert isinstance(token, str)
    
    @pytest.mark.asyncio
    async def test_refresh_token_has_correct_type(self):
        """Refresh tokens should have type='refresh' claim."""
        from app.auth import create_refresh_token
        from jose import jwt
        from app.core.config import settings
        
        token = create_refresh_token({"sub": "test@example.com"})
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        assert payload.get("type") == "refresh"


class TestSecurityConfiguration:
    """Test security configuration validation."""
    
    def test_jwt_secret_required(self):
        """JWT_SECRET_KEY should be required (no default)."""
        from app.core.config import Settings
        from pydantic import ValidationError
        
        # Should raise error if JWT_SECRET_KEY not provided
        with pytest.raises(ValidationError):
            Settings(_env_file=None)
    
    def test_cookie_defaults_secure(self):
        """Cookie settings should default to secure values."""
        from app.core.config import settings
        
        assert settings.COOKIE_SECURE is True
        assert settings.COOKIE_HTTPONLY is True
        assert settings.COOKIE_SAMESITE in ("lax", "strict")
    
    def test_debug_defaults_false(self):
        """Debug should default to False."""
        from app.core.config import settings
        
        assert settings.DEBUG is False
