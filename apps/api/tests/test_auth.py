"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient

from app.auth import hash_password
from app.db.models import User
from app.db.session import AsyncSessionLocal


@pytest.fixture
async def test_user_data():
    """Test user credentials."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!"
    }


@pytest.fixture
async def created_user(test_user_data, db_cleanup):
    """Create a test user in the database."""
    async with AsyncSessionLocal() as session:
        from uuid import uuid4
        user = User(
            id=str(uuid4()),
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=hash_password(test_user_data["password"]),
            role="user",
            active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
async def auth_token(api_client: AsyncClient, test_user_data, created_user):
    """Get authentication token for test user."""
    response = await api_client.post(
        "/auth/login",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


class TestUserRegistration:
    """Tests for user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_new_user_success(self, api_client: AsyncClient, db_cleanup):
        """Test successful user registration."""
        response = await api_client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePassword123!"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"
        assert data["active"] is True
        assert "created_at" in data
        
        # Verify password is not in response
        assert "password" not in data
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, api_client: AsyncClient, created_user, test_user_data):
        """Test registration with duplicate username fails."""
        response = await api_client.post(
            "/auth/register",
            json={
                "username": test_user_data["username"],
                "email": "different@example.com",
                "password": "SecurePassword123!"
            }
        )
        
        assert response.status_code == 400
        assert "username already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, api_client: AsyncClient, created_user, test_user_data):
        """Test registration with duplicate email fails."""
        response = await api_client.post(
            "/auth/register",
            json={
                "username": "differentuser",
                "email": test_user_data["email"],
                "password": "SecurePassword123!"
            }
        )
        
        assert response.status_code == 400
        assert "email already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, api_client: AsyncClient, db_cleanup):
        """Test registration with invalid email fails."""
        response = await api_client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "password": "SecurePassword123!"
            }
        )
        
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_short_password(self, api_client: AsyncClient, db_cleanup):
        """Test registration with short password fails."""
        response = await api_client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "short"
            }
        )
        
        assert response.status_code == 422  # Validation error
        assert "at least 8 characters" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, api_client: AsyncClient, db_cleanup):
        """Test registration with missing fields fails."""
        response = await api_client.post(
            "/auth/register",
            json={
                "username": "newuser"
                # Missing email and password
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Tests for user login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, api_client: AsyncClient, created_user, test_user_data):
        """Test successful login."""
        response = await api_client.post(
            "/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 50  # JWT tokens are long

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, api_client: AsyncClient, created_user, test_user_data):
        """Test login with wrong password fails."""
        response = await api_client.post(
            "/auth/login",
            json={
                "email": test_user_data["email"],
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, api_client: AsyncClient, db_cleanup):
        """Test login with non-existent email fails."""
        response = await api_client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123!"
            }
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_invalid_email_format(self, api_client: AsyncClient, db_cleanup):
        """Test login with invalid email format fails."""
        response = await api_client.post(
            "/auth/login",
            json={
                "email": "not-an-email",
                "password": "SomePassword123!"
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestGetCurrentUser:
    """Tests for get current user endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, api_client: AsyncClient, auth_token, test_user_data):
        """Test getting current user with valid token."""
        response = await api_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["role"] == "user"
        assert data["active"] is True
        assert "id" in data
        assert "created_at" in data
        
        # Verify password is not in response
        assert "password" not in data
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, api_client: AsyncClient):
        """Test getting current user without token returns null (optional auth)."""
        response = await api_client.get("/auth/me")
        
        # Based on optional auth implementation, this might return 200 with null or 401
        # Adjust based on your actual implementation
        assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, api_client: AsyncClient):
        """Test getting current user with invalid token fails."""
        response = await api_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        assert response.status_code == 401
        assert "credentials" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, api_client: AsyncClient):
        """Test getting current user with expired token fails."""
        # This is a token that has already expired
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxfQ.invalid"
        
        response = await api_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_malformed_header(self, api_client: AsyncClient, auth_token):
        """Test getting current user with malformed auth header fails."""
        # Missing "Bearer" prefix
        response = await api_client.get(
            "/auth/me",
            headers={"Authorization": auth_token}
        )
        
        # Should fail due to malformed header
        assert response.status_code in [401, 403]


class TestAuthenticationIntegration:
    """Integration tests for authentication flow."""

    @pytest.mark.asyncio
    async def test_full_registration_login_flow(self, api_client: AsyncClient, db_cleanup):
        """Test complete flow: register -> login -> access protected endpoint."""
        # Step 1: Register
        register_response = await api_client.post(
            "/auth/register",
            json={
                "username": "flowtest",
                "email": "flowtest@example.com",
                "password": "FlowTest123!"
            }
        )
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]
        
        # Step 2: Login
        login_response = await api_client.post(
            "/auth/login",
            json={
                "email": "flowtest@example.com",
                "password": "FlowTest123!"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Step 3: Access protected endpoint
        me_response = await api_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["id"] == user_id
        assert me_response.json()["email"] == "flowtest@example.com"

    @pytest.mark.asyncio
    async def test_token_reuse(self, api_client: AsyncClient, auth_token, test_user_data):
        """Test that the same token can be reused multiple times."""
        # First request
        response1 = await api_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response1.status_code == 200
        
        # Second request with same token
        response2 = await api_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response2.status_code == 200
        
        # Verify both responses are identical
        assert response1.json() == response2.json()

    @pytest.mark.asyncio
    async def test_multiple_users_independent(self, api_client: AsyncClient, db_cleanup):
        """Test that multiple users can register and login independently."""
        # Create first user
        await api_client.post(
            "/auth/register",
            json={
                "username": "user1",
                "email": "user1@example.com",
                "password": "Password123!"
            }
        )
        
        # Create second user
        await api_client.post(
            "/auth/register",
            json={
                "username": "user2",
                "email": "user2@example.com",
                "password": "Password123!"
            }
        )
        
        # Login as user1
        login1 = await api_client.post(
            "/auth/login",
            json={
                "email": "user1@example.com",
                "password": "Password123!"
            }
        )
        token1 = login1.json()["access_token"]
        
        # Login as user2
        login2 = await api_client.post(
            "/auth/login",
            json={
                "email": "user2@example.com",
                "password": "Password123!"
            }
        )
        token2 = login2.json()["access_token"]
        
        # Verify tokens are different
        assert token1 != token2
        
        # Verify each token returns correct user
        me1 = await api_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert me1.json()["email"] == "user1@example.com"
        
        me2 = await api_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert me2.json()["email"] == "user2@example.com"


class TestPasswordSecurity:
    """Tests for password security."""

    @pytest.mark.asyncio
    async def test_password_not_stored_plaintext(self, api_client: AsyncClient, db_cleanup):
        """Test that passwords are hashed, not stored in plaintext."""
        password = "SecurePassword123!"
        
        # Register user
        await api_client.post(
            "/auth/register",
            json={
                "username": "sectest",
                "email": "sectest@example.com",
                "password": password
            }
        )
        
        # Check database directly
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email == "sectest@example.com")
            )
            user = result.scalars().first()
            
            # Password hash should not equal plaintext password
            assert user.password_hash != password
            
            # Password hash should be bcrypt format
            assert user.password_hash.startswith("$2b$")
            
            # Password hash should be long
            assert len(user.password_hash) > 50

    @pytest.mark.asyncio
    async def test_same_password_different_hashes(self, api_client: AsyncClient, db_cleanup):
        """Test that the same password produces different hashes (salt)."""
        password = "SamePassword123!"
        
        # Register two users with same password
        await api_client.post(
            "/auth/register",
            json={
                "username": "salt1",
                "email": "salt1@example.com",
                "password": password
            }
        )
        
        await api_client.post(
            "/auth/register",
            json={
                "username": "salt2",
                "email": "salt2@example.com",
                "password": password
            }
        )
        
        # Check that hashes are different (due to salt)
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email.in_(["salt1@example.com", "salt2@example.com"]))
            )
            users = result.scalars().all()
            
            assert len(users) == 2
            assert users[0].password_hash != users[1].password_hash
