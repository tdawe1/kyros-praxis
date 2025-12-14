"""Security tests for authentication and authorization fixes.

Tests for critical security vulnerabilities that were identified and fixed:
- P0: Unauthenticated project update/delete
- P0: Unauthenticated shared memory access
- P1: WebSocket token type enforcement
- P1: Batch run creation authentication
"""

import pytest
import pytest_asyncio
from fastapi import status
from sqlalchemy import select

from app.auth import create_access_token, create_refresh_token
from app.db.models import Project, User
from app.db.session import AsyncSessionLocal


class TestProjectAuthorization:
    """Test authorization for project endpoints (P0-CRITICAL fix)."""
    
    @pytest.mark.asyncio
    async def test_update_project_requires_auth(self, api_client, test_project):
        """Test that updating a project requires authentication."""
        response = await api_client.patch(
            f"/projects/{test_project.id}",
            json={"name": "Hacked Project"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "authentication required" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_update_project_requires_ownership(self, api_client, test_project, test_user, test_db):
        """Test that updating a project requires ownership."""
        # Create another user
        other_user = User(
            id="other-user-id",
            email="other@example.com",
            username="other",
            password_hash="hashed",
            active=True
        )
        test_db.add(other_user)
        await test_db.commit()
        
        # Try to update project as different user
        token = create_access_token(data={"sub": other_user.email})
        response = await api_client.patch(
            f"/projects/{test_project.id}",
            json={"name": "Hacked Project"},
            cookies={"access_token": token}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "not authorized" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_update_project_succeeds_for_owner(self, api_client, test_project, test_user):
        """Test that project owner can update their project."""
        token = create_access_token(data={"sub": test_user.email})
        response = await api_client.patch(
            f"/projects/{test_project.id}",
            json={"name": "Updated Project"},
            cookies={"access_token": token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Updated Project"
    
    @pytest.mark.asyncio
    async def test_delete_project_requires_auth(self, api_client, test_project):
        """Test that deleting a project requires authentication."""
        response = await api_client.delete(f"/projects/{test_project.id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_delete_project_requires_ownership(self, api_client, test_project, test_user, test_db):
        """Test that deleting a project requires ownership."""
        # Create another user
        other_user = User(
            id="other-user-id-2",
            email="other2@example.com",
            username="other2",
            hashed_password="hashed",
            active=True
        )
        test_db.add(other_user)
        await test_db.commit()
        
        # Try to delete project as different user
        token = create_access_token(data={"sub": other_user.email})
        response = await api_client.delete(
            f"/projects/{test_project.id}",
            cookies={"access_token": token}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "not authorized" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_project_succeeds_for_owner(self, api_client, test_project, test_user, test_db):
        """Test that project owner can delete their project."""
        token = create_access_token(data={"sub": test_user.email})
        response = await api_client.delete(
            f"/projects/{test_project.id}",
            cookies={"access_token": token}
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify project is deleted
        result = await test_db.execute(
            select(Project).where(Project.id == test_project.id)
        )
        assert result.scalars().first() is None


class TestSharedMemoryAuthorization:
    """Test authorization for shared memory endpoints (P0-CRITICAL fix)."""
    
    @pytest.mark.asyncio
    async def test_set_memory_requires_auth(self, api_client):
        """Test that setting memory requires authentication."""
        response = await api_client.post(
            "/memory/set",
            json={
                "project_id": "test-project",
                "key": "test-key",
                "value": "test-value"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_set_memory_requires_project_access(self, api_client, test_project, test_user, test_db):
        """Test that setting memory requires project access."""
        # Create another user
        other_user = User(
            id="other-user-id-3",
            email="other3@example.com",
            username="other3",
            hashed_password="hashed",
            active=True
        )
        test_db.add(other_user)
        await test_db.commit()
        
        # Try to set memory as different user
        token = create_access_token(data={"sub": other_user.email})
        response = await api_client.post(
            "/memory/set",
            json={
                "project_id": test_project.id,
                "key": "test-key",
                "value": "test-value"
            },
            cookies={"access_token": token}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "not authorized" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_memory_requires_auth(self, api_client):
        """Test that getting memory requires authentication."""
        response = await api_client.post(
            "/memory/get",
            json={
                "project_id": "test-project",
                "key": "test-key"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_all_memory_requires_auth(self, api_client):
        """Test that getting all memory requires authentication."""
        response = await api_client.get("/memory/test-project/all")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_delete_memory_requires_auth(self, api_client):
        """Test that deleting memory requires authentication."""
        response = await api_client.delete("/memory/test-project/test-key")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_publish_event_requires_auth(self, api_client):
        """Test that publishing events requires authentication."""
        response = await api_client.post(
            "/memory/publish",
            json={
                "project_id": "test-project",
                "event_type": "test",
                "payload": {}
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_subscribe_events_requires_auth(self, api_client):
        """Test that subscribing to events requires authentication."""
        response = await api_client.get("/memory/test-project/events")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenTypeEnforcement:
    """Test token type enforcement (P1-HIGH fix)."""
    
    @pytest.mark.asyncio
    async def test_ws_token_rejected_for_api_endpoints(self, api_client, test_user):
        """Test that WebSocket tokens are rejected for regular API endpoints."""
        # Create a WebSocket token (type="ws")
        ws_token = create_access_token(
            data={"sub": test_user.email, "type": "ws"}
        )
        
        # Try to use it on a regular API endpoint
        response = await api_client.get(
            "/projects",
            cookies={"access_token": ws_token}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid token type" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_refresh_token_rejected_for_api_endpoints(self, api_client, test_user):
        """Test that refresh tokens are rejected for regular API endpoints."""
        # Create a refresh token (type="refresh")
        refresh_token = create_refresh_token(data={"sub": test_user.email})
        
        # Try to use it on a regular API endpoint
        response = await api_client.get(
            "/projects",
            cookies={"access_token": refresh_token}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_access_token_accepted_for_api_endpoints(self, api_client, test_user):
        """Test that access tokens work correctly for regular API endpoints."""
        # Create a proper access token (type="access")
        access_token = create_access_token(data={"sub": test_user.email})
        
        # Should work fine
        response = await api_client.get(
            "/projects",
            cookies={"access_token": access_token}
        )
        
        assert response.status_code == status.HTTP_200_OK


class TestBatchRunAuthorization:
    """Test authorization for batch run endpoints (P1-HIGH fix)."""
    
    @pytest.mark.asyncio
    async def test_create_batch_runs_requires_auth(self, api_client):
        """Test that creating batch runs requires authentication."""
        response = await api_client.post(
            "/batch/runs",
            json={
                "project_id": "test-project",
                "tasks": []
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_create_batch_runs_requires_ownership(self, api_client, test_project, test_user, test_db):
        """Test that creating batch runs requires project ownership."""
        # Create another user
        other_user = User(
            id="other-user-id-4",
            email="other4@example.com",
            username="other4",
            hashed_password="hashed",
            active=True
        )
        test_db.add(other_user)
        await test_db.commit()
        
        # Try to create batch runs as different user
        token = create_access_token(data={"sub": other_user.email})
        response = await api_client.post(
            "/batch/runs",
            json={
                "project_id": test_project.id,
                "tasks": []
            },
            cookies={"access_token": token}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "not authorized" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_batch_status_requires_auth(self, api_client):
        """Test that getting batch status requires authentication."""
        response = await api_client.get("/batch/runs/test-batch/status")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_cancel_batch_requires_auth(self, api_client):
        """Test that cancelling batch requires authentication."""
        response = await api_client.post("/batch/cancel/test-batch")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Fixtures for tests

@pytest_asyncio.fixture
async def test_db():
    """Create a test database session."""
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(test_db):
    """Create a test user."""
    user = User(
        id="test-user-id",
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        active=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_project(test_db, test_user):
    """Create a test project owned by test_user."""
    project = Project(
        id="test-project-id",
        name="Test Project",
        description="Test Description",
        status="planning",
        created_by=test_user.id
    )
    test_db.add(project)
    await test_db.commit()
    await test_db.refresh(project)
    return project
