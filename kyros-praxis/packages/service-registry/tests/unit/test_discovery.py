import pytest

from packages.service_registry.main import get_service, register_service


def test_service_registration():
    service = {"id": "svc1", "endpoint": "http://test:8000"}
    register_service(service)
    assert get_service("svc1") == service

    # Duplicate ID test
    with pytest.raises(KeyError):
        register_service({"id": "svc1", "endpoint": "http://other:8000"})
