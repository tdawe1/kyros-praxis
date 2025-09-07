#!/usr/bin/env python3
"""
Script to validate the orchestrator API specification and endpoints.
Run this to ensure the API matches the OpenAPI spec.
"""

import os
import time
from pathlib import Path

import httpx
import yaml

project_root = Path(__file__).parent.parent


def validate_openapi_spec() -> bool:
    spec_path = project_root / "api-specs" / "orchestrator-v1.yaml"
    if not spec_path.exists():
        print("❌ API spec file not found:", spec_path)
        return False
    try:
        with open(spec_path, "r") as f:
            spec = yaml.safe_load(f)
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            if field not in spec:
                print(f"❌ Missing required field: {field}")
                return False
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


def validate_endpoints() -> bool:
    base_url = os.environ.get("BASE_URL", "http://127.0.0.1:8080")
    token = os.environ.get("DEV_JWT")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        with httpx.Client(base_url=base_url, timeout=5.0) as client:
            for _ in range(5):
                try:
                    health_response = client.get("/healthz", headers=headers)
                    break
                except httpx.RequestError:
                    time.sleep(1)
            else:
                print("❌ /healthz endpoint failed")
                return False
            if health_response.status_code != 200 or health_response.json() != {
                "ok": True
            }:
                print("❌ /healthz endpoint failed")
                return False
            print("✅ /healthz endpoint working")

            ready_response = client.get("/readyz", headers=headers)
            if ready_response.status_code != 200 or ready_response.json() != {
                "ready": True
            }:
                print("❌ /readyz endpoint failed")
                return False
            print("✅ /readyz endpoint working")

            config_response = client.get("/v1/config", headers=headers)
            if config_response.status_code != 200:
                print("❌ /v1/config endpoint failed")
                return False
            config_data = config_response.json()
            for key in ["services", "agents", "log"]:
                if key not in config_data:
                    print(f"❌ /v1/config missing key: {key}")
                    return False
            print("✅ /v1/config endpoint working")

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
            plan_response = client.post(
                "/v1/runs/plan", json=plan_data, headers=headers
            )
            if plan_response.status_code != 200:
                print("❌ /v1/runs/plan endpoint failed")
                return False
            plan_result = plan_response.json()
            for key in ["run_id", "status", "started_at"]:
                if key not in plan_result:
                    print(f"❌ /v1/runs/plan missing key: {key}")
                    return False
            print("✅ /v1/runs/plan endpoint working")
            return True
    except Exception as e:
        print(f"❌ Error validating endpoints: {e}")
        return False


def main() -> int:
    print("🔍 Validating Kyros Orchestrator API...\n")
    spec_valid = validate_openapi_spec()
    print()
    endpoints_valid = validate_endpoints()
    print()
    if spec_valid and endpoints_valid:
        print("🎉 All validations passed! API is ready.")
        return 0
    print("❌ Some validations failed. Please fix the issues above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
