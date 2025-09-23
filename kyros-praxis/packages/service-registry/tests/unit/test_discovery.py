import os
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from packages.service_registry.main import app, get_current_user, get_db
from packages.service_registry.models import Base


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "test-user"}
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(autouse=True)
def override_db(tmp_path: Path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def get_test_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()
    if db_path.exists():
        os.remove(db_path)


@pytest.mark.asyncio
async def test_service_registration():
    async with AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "name": "svc1",
            "host": "test",
            "port": "8000",
            "capabilities": {"health": "ok"},
        }
        response = await client.post("/register", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body == {"status": "registered", "service": "svc1"}

        list_response = await client.get("/services")
        assert list_response.status_code == 200
        services = list_response.json()["services"]
        assert any(service["name"] == "svc1" for service in services)
