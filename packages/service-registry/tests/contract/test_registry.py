import pytest

from httpx import AsyncClient

from packages.service_registry.main import app


TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMSJ9.signature"  # Shortened dummy token


@pytest.mark.asyncio
async def test_register_service_contract():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/register",
            json={"id": "svc1", "endpoint": "http://test:8000"},
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_services_contract():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/services",
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        assert response.status_code == 200
        assert "services" in response.json()


@pytest.mark.asyncio
async def test_unregister_service_contract():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete(
            "/unregister/svc1",
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_contract():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/health/svc1",
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        assert response.status_code == 200
        assert "status" in response.json()