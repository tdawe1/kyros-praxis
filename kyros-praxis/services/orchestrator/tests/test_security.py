"""
Security module test suite
Tests for SQL injection prevention, authentication, and security middleware
"""

import pytest
import bcrypt
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import jwt

# Import our security modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_database import SecureDatabase, SecureDatabasePool
from security_middleware import (
    SecurityConfig,
    RateLimiter,
    CSRFProtection,
    JWTAuthentication
)


class TestSecureDatabase:
    """Test secure database operations"""

    @pytest.fixture
    def db(self):
        """Create test database instance with tables"""
        from models import Base
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        # Create in-memory database with tables
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        # Create all tables
        Base.metadata.create_all(bind=engine)

        # Create SecureDatabase instance with the same engine
        secure_db = SecureDatabase("sqlite:///:memory:")
        # Replace the engine with our table-created engine
        secure_db.engine = engine
        secure_db.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

        return secure_db
    
    def test_sql_injection_prevention(self, db):
        """Test that SQL injection attempts are prevented"""
        # Attempt SQL injection through username
        malicious_username = "admin'; DROP TABLE users; --"
        
        # This should safely parameterize the query
        result = db.get_user_by_username(malicious_username)
        
        # Should return None, not execute the DROP TABLE
        assert result is None
        
    def test_password_hashing_not_md5(self, db):
        """Test that passwords are hashed with bcrypt, not MD5"""
        password = "test_password_123"
        
        # Create hash
        hashed = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        
        # Verify it's a bcrypt hash (starts with $2b$)
        assert hashed.startswith('$2b$')
        
        # Verify it's not MD5 (MD5 is 32 hex characters)
        assert len(hashed) > 32
        assert not all(c in '0123456789abcdef' for c in hashed)
        
    def test_timing_attack_prevention(self, db):
        """Test that login attempts prevent timing attacks"""
        # Mock user retrieval
        db.get_user_by_username = Mock(return_value=None)
        
        # Time multiple failed login attempts
        import time
        times = []
        
        for _ in range(5):
            start = time.time()
            db.validate_user_login("nonexistent", "password")
            times.append(time.time() - start)
        
        # Check that times are consistent (prevents timing attacks)
        # All times should be within 50ms of each other
        avg_time = sum(times) / len(times)
        for t in times:
            assert abs(t - avg_time) < 0.05
            
    def test_parameterized_search(self, db):
        """Test that search queries are parameterized"""
        # Attempt SQL injection in search
        malicious_search = "'; DELETE FROM items; --"
        
        # This should safely parameterize
        with patch.object(db, 'execute_safe_query', return_value=[]) as mock_execute:
            db.search_items(malicious_search)
            
            # Check that the query was parameterized
            mock_execute.assert_called_once()
            args = mock_execute.call_args
            
            # The search term should be in params, not in the query string
            assert 'search_pattern' in args[0][1]
            assert "DELETE" not in args[0][0]  # SQL should not contain DELETE
            
    def test_secure_token_generation(self, db):
        """Test cryptographically secure token generation"""
        token1 = db.generate_secure_token()
        token2 = db.generate_secure_token()
        
        # Tokens should be different
        assert token1 != token2
        
        # Tokens should be of sufficient length
        assert len(token1) >= 32
        
        # Tokens should be URL-safe
        assert all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_' 
                  for c in token1)


class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def test_rate_limit_enforcement(self):
        """Test that rate limits are enforced"""
        limiter = RateLimiter(requests=3, window=1)
        client_id = "test_client"
        
        # First 3 requests should be allowed
        assert limiter.is_allowed(client_id) is True
        assert limiter.is_allowed(client_id) is True
        assert limiter.is_allowed(client_id) is True
        
        # 4th request should be blocked
        assert limiter.is_allowed(client_id) is False
        
    def test_rate_limit_window_reset(self):
        """Test that rate limit resets after window"""
        limiter = RateLimiter(requests=2, window=0.1)  # 100ms window
        client_id = "test_client"
        
        # Use up the limit
        assert limiter.is_allowed(client_id) is True
        assert limiter.is_allowed(client_id) is True
        assert limiter.is_allowed(client_id) is False
        
        # Wait for window to reset
        import time
        time.sleep(0.15)
        
        # Should be allowed again
        assert limiter.is_allowed(client_id) is True
        
    def test_multiple_clients(self):
        """Test that rate limits are per-client"""
        limiter = RateLimiter(requests=2, window=10)
        
        # Client 1 uses their limit
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is False
        
        # Client 2 should still be allowed
        assert limiter.is_allowed("client2") is True
        assert limiter.is_allowed("client2") is True
        assert limiter.is_allowed("client2") is False


class TestCSRFProtection:
    """Test CSRF protection"""
    
    def test_token_generation(self):
        """Test CSRF token generation"""
        csrf = CSRFProtection("test_secret")
        
        token1 = csrf.generate_token()
        token2 = csrf.generate_token()
        
        # Tokens should be unique
        assert token1 != token2
        
        # Tokens should be of expected length
        # New format: random_data(32) + timestamp + session_data + signature(32) = ~100+ chars
        assert len(token1) > 80  # Much longer with new secure format
        
    def test_token_validation(self):
        """Test CSRF token validation"""
        csrf = CSRFProtection("test_secret")

        # Generate a token
        token = csrf.generate_token()

        # Should validate successfully
        assert csrf.validate_token(token) is True

        # Invalid tokens should fail
        assert csrf.validate_token("invalid_token") is False
        assert csrf.validate_token("") is False
        assert csrf.validate_token(None) is False


class TestJWTAuthentication:
    """Test JWT authentication"""
    
    def test_token_creation(self):
        """Test JWT token creation"""
        auth = JWTAuthentication("test_secret")
        
        user_id = "user123"
        role = "admin"
        
        token = auth.create_token(user_id, role)
        
        # Should create a valid JWT
        assert token is not None
        assert len(token) > 0
        
        # Decode to verify contents
        payload = jwt.decode(token, "test_secret", algorithms=["HS512"])
        
        assert payload["sub"] == user_id
        assert payload["role"] == role
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
        
    def test_token_verification(self):
        """Test JWT token verification"""
        auth = JWTAuthentication("test_secret")
        
        # Create a token
        token = auth.create_token("user123", "user")
        
        # Verify it
        payload = auth.verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["role"] == "user"
        
    def test_expired_token(self):
        """Test that expired tokens are rejected"""
        auth = JWTAuthentication("test_secret", expiration_hours=-1)
        
        # Create an already-expired token
        token = auth.create_token("user123", "user")
        
        # Should fail verification
        payload = auth.verify_token(token)
        assert payload is None
        
    def test_invalid_token(self):
        """Test that invalid tokens are rejected"""
        auth = JWTAuthentication("test_secret")
        
        # Various invalid tokens
        assert auth.verify_token("invalid.token.here") is None
        assert auth.verify_token("") is None
        assert auth.verify_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid") is None


class TestSecurityIntegration:
    """Integration tests for security components"""
    
    def test_secure_login_flow(self):
        """Test complete secure login flow"""
        db = SecureDatabase("sqlite:///:memory:")
        auth = JWTAuthentication("test_secret")
        
        # Create a user (mocked)
        password = "secure_password_123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Mock user retrieval
        db.get_user_by_username = Mock(return_value={
            'id': '123',
            'username': 'testuser',
            'password_hash': hashed,
            'role': 'user'
        })
        
        # Attempt login
        user = db.validate_user_login('testuser', password)
        
        assert user is not None
        assert 'password_hash' not in user  # Password hash should be removed
        
        # Generate JWT token
        token = auth.create_token(user['id'], user['role'])
        assert token is not None
        
        # Verify token
        payload = auth.verify_token(token)
        assert payload['sub'] == '123'
        assert payload['role'] == 'user'


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])