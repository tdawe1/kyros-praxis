#!/usr/bin/env python3
"""
Script to validate the orchestrator API specification and endpoints.
Run this to ensure the API matches the OpenAPI spec.
"""

import sys
from pathlib import Path

import yaml

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def validate_openapi_spec():
    """Validate the OpenAPI specification file."""
    spec_path = project_root / "api-specs" / "orchestrator-v1.yaml"

    if not spec_path.exists():
        print("❌ API spec file not found:", spec_path)
        return False

    try:
        with open(spec_path, "r") as f:
            spec = yaml.safe_load(f)

        # Basic validation
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            if field not in spec:
                print(f"❌ Missing required field: {field}")
                return False

        # Check for required endpoints
        required_endpoints = ["/healthz", "/readyz", "/v1/config", "/v1/runs/plan"]
        for endpoint in required_endpoints:
            if endpoint not in spec.get("paths", {}):
                print(f"❌ Missing required endpoint: {endpoint}")
                return False

        print("✅ OpenAPI specification is valid")
        return True

    except Exception as e:
        print(f"❌ Error validating OpenAPI spec: {e}")
        return False


def validate_endpoints():
    """Validate that the FastAPI endpoints work correctly."""
    try:
        # Add the apps directory to the path
        apps_path = project_root / "apps" / "adk-orchestrator"
        sys.path.insert(0, str(apps_path))

        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Test health endpoints
        health_response = client.get("/healthz")
        if health_response.status_code != 200 or health_response.json() != {"ok": True}:
            print("❌ /healthz endpoint failed")
            return False
        print("✅ /healthz endpoint working")

        ready_response = client.get("/readyz")
        if ready_response.status_code != 200 or ready_response.json() != {
            "ready": True
        }:
            print("❌ /readyz endpoint failed")
            return False
        print("✅ /readyz endpoint working")

        # Test config endpoint
        config_response = client.get("/v1/config")
        if config_response.status_code != 200:
            print("❌ /v1/config endpoint failed")
            return False

        config_data = config_response.json()
        required_config_keys = ["services", "agents", "log"]
        for key in required_config_keys:
            if key not in config_data:
                print(f"❌ /v1/config missing key: {key}")
                return False
        print("✅ /v1/config endpoint working")

        # Test plan endpoint
        plan_data = {
            "pr": {
                "repo": "test/repo",
                "pr_number": 123,
                "branch": "feature/test",
                "head_sha": "abc123",
            },
            "mode": "plan",
            "labels": ["test"],
            "extra": {},
        }

        plan_response = client.post("/v1/runs/plan", json=plan_data)
        if plan_response.status_code != 200:
            print("❌ /v1/runs/plan endpoint failed")
            return False

        plan_result = plan_response.json()
        required_plan_keys = ["run_id", "status", "started_at"]
        for key in required_plan_keys:
            if key not in plan_result:
                print(f"❌ /v1/runs/plan missing key: {key}")
                return False
        print("✅ /v1/runs/plan endpoint working")

        return True

    except Exception as e:
        print(f"❌ Error validating endpoints: {e}")
        return False


def main():
    """Main validation function."""
    print("🔍 Validating Kyros Orchestrator API...")
    print()

    # Validate OpenAPI spec
    spec_valid = validate_openapi_spec()
    print()

    # Validate endpoints
    endpoints_valid = validate_endpoints()
    print()

    if spec_valid and endpoints_valid:
        print("🎉 All validations passed! API is ready.")
        return 0
    else:
        print("❌ Some validations failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
