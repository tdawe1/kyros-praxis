"""
Integration tests for role-based access control with FastAPI endpoints.

These tests verify that the role-based access control system works correctly
with actual FastAPI endpoints, testing the complete authentication and
authorization flow.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.orchestrator.database import get_db
from services.orchestrator.models import Base, User
from services.orchestrator.auth import pwd_context, create_access_token
from services.orchestrator.main import app


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_roles.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_test_db():
    """Override get_db dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override dependency
app.dependency_overrides[get_db] = get_test_db


class TestRoleBasedEndpoints:
    """Integration tests for role-based access control endpoints."""
    
    @pytest.fixture(scope="class")
    def setup_database(self):
        """Set up test database and users."""
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Create test session
        db = TestingSessionLocal()
        
        # Create test users with different roles
        users = {
            "user": User(
                username="testuser",
                email="user@test.com",
                password_hash=pwd_context.hash("password123"),
                role="user",
                active=1
            ),
            "moderator": User(
                username="testmod",
                email="mod@test.com", 
                password_hash=pwd_context.hash("password123"),
                role="moderator",
                active=1
            ),
            "admin": User(
                username="testadmin",
                email="admin@test.com",
                password_hash=pwd_context.hash("password123"),
                role="admin",
                active=1
            )
        }
        
        for user in users.values():
            db.add(user)
        
        db.commit()
        db.close()
        
        yield users
        
        # Cleanup
        Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def get_auth_headers(self, username: str) -> dict:
        """Get authentication headers for a user."""
        token = create_access_token(data={"sub": username})
        return {"Authorization": f"Bearer {token}"}
    
    def test_user_can_access_user_content(self, client, setup_database):
        """Test that user role can access user content endpoint."""
        headers = self.get_auth_headers("testuser")
        response = client.get("/api/v1/examples/user-content", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "user"
        assert data["user"]["role"] == "user"
        assert "accessible to all authenticated users" in data["message"]
    
    def test_moderator_can_access_user_content(self, client, setup_database):
        """Test that moderator role can access user content endpoint."""
        headers = self.get_auth_headers("testmod")
        response = client.get("/api/v1/examples/user-content", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "user"
        assert data["user"]["role"] == "moderator"
    
    def test_admin_can_access_user_content(self, client, setup_database):
        """Test that admin role can access user content endpoint."""
        headers = self.get_auth_headers("testadmin")
        response = client.get("/api/v1/examples/user-content", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "user"
        assert data["user"]["role"] == "admin"
    
    def test_user_cannot_access_moderator_content(self, client, setup_database):
        """Test that user role cannot access moderator content endpoint."""
        headers = self.get_auth_headers("testuser")
        response = client.get("/api/v1/examples/moderator-content", headers=headers)
        
        assert response.status_code == 403
        data = response.json()
        assert "Access denied" in data["detail"]
        assert "Required role: moderator" in data["detail"]
        assert "user role: user" in data["detail"]
    
    def test_moderator_can_access_moderator_content(self, client, setup_database):
        """Test that moderator role can access moderator content endpoint."""
        headers = self.get_auth_headers("testmod")
        response = client.get("/api/v1/examples/moderator-content", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "moderator"
        assert data["user"]["role"] == "moderator"
        assert "elevated permissions" in data["message"]
    
    def test_admin_can_access_moderator_content(self, client, setup_database):
        """Test that admin role can access moderator content endpoint."""
        headers = self.get_auth_headers("testadmin")
        response = client.get("/api/v1/examples/moderator-content", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "moderator"
        assert data["user"]["role"] == "admin"
    
    def test_user_cannot_access_admin_content(self, client, setup_database):
        """Test that user role cannot access admin content endpoint."""
        headers = self.get_auth_headers("testuser")
        response = client.get("/api/v1/examples/admin-content", headers=headers)
        
        assert response.status_code == 403
        data = response.json()
        assert "Access denied" in data["detail"]
        assert "Required role: admin" in data["detail"]
    
    def test_moderator_cannot_access_admin_content(self, client, setup_database):
        """Test that moderator role cannot access admin content endpoint."""
        headers = self.get_auth_headers("testmod")
        response = client.get("/api/v1/examples/admin-content", headers=headers)
        
        assert response.status_code == 403
        data = response.json()
        assert "Access denied" in data["detail"]
        assert "Required role: admin" in data["detail"]
        assert "user role: moderator" in data["detail"]
    
    def test_admin_can_access_admin_content(self, client, setup_database):
        """Test that admin role can access admin content endpoint."""
        headers = self.get_auth_headers("testadmin")
        response = client.get("/api/v1/examples/admin-content", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "admin"
        assert data["user"]["role"] == "admin"
        assert "full system access" in data["message"]
    
    def test_exact_role_moderator_tools(self, client, setup_database):
        """Test exact role matching for moderator tools."""
        # User cannot access
        headers = self.get_auth_headers("testuser")
        response = client.get("/api/v1/examples/moderator-tools", headers=headers)
        assert response.status_code == 403
        
        # Moderator can access
        headers = self.get_auth_headers("testmod")
        response = client.get("/api/v1/examples/moderator-tools", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "moderator-exact"
        assert "User management dashboard" in data["tools"]
        
        # Admin cannot access (exact role only)
        headers = self.get_auth_headers("testadmin")
        response = client.get("/api/v1/examples/moderator-tools", headers=headers)
        assert response.status_code == 403
        data = response.json()
        assert "Required exact role: moderator" in data["detail"]
        assert "user role: admin" in data["detail"]
    
    def test_role_info_endpoint(self, client, setup_database):
        """Test role information endpoint shows correct permissions."""
        # Test user role info
        headers = self.get_auth_headers("testuser")
        response = client.get("/api/v1/examples/role-info", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["user"]["role"] == "user"
        assert data["role_hierarchy"]["current_level"] == 0  # User is level 0
        assert data["accessible_endpoints"] == ["user-content"]
        assert data["permissions"]["can_access_user_content"] is True
        assert data["permissions"]["can_access_moderator_content"] is False
        assert data["permissions"]["can_access_admin_content"] is False
        
        # Test moderator role info
        headers = self.get_auth_headers("testmod")
        response = client.get("/api/v1/examples/role-info", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["user"]["role"] == "moderator"
        assert data["role_hierarchy"]["current_level"] == 1  # Moderator is level 1
        assert "user-content" in data["accessible_endpoints"]
        assert "moderator-content" in data["accessible_endpoints"]
        assert "admin-content" not in data["accessible_endpoints"]
        assert "moderator-tools" in data["exact_role_endpoints"]
        
        # Test admin role info
        headers = self.get_auth_headers("testadmin")
        response = client.get("/api/v1/examples/role-info", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["user"]["role"] == "admin"
        assert data["role_hierarchy"]["current_level"] == 2  # Admin is level 2
        assert len(data["accessible_endpoints"]) == 3  # Can access all content types
        assert data["permissions"]["can_access_admin_content"] is True
    
    def test_unauthenticated_access_denied(self, client, setup_database):
        """Test that unauthenticated users are denied access."""
        # No authorization header
        response = client.get("/api/v1/examples/user-content")
        assert response.status_code == 401
        
        # Invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/examples/user-content", headers=headers)
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])