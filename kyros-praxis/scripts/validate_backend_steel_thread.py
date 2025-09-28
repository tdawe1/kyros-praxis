#!/usr/bin/env python3
"""
Validation script for Backend Steel Thread implementation.
This script validates that all required components are implemented and working.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_models():
    """Validate that Task model is properly implemented."""
    print("🔍 Validating Task model...")
    try:
        from services.orchestrator.models import Task
        from sqlalchemy import inspect

        # Check Task model has required fields
        mapper = inspect(Task)
        columns = [c.name for c in mapper.columns]
        required_columns = ['id', 'title', 'description', 'version', 'created_at']

        missing_columns = [col for col in required_columns if col not in columns]
        if missing_columns:
            print(f"❌ Task model missing columns: {missing_columns}")
            return False

        print("✅ Task model properly implemented")
        return True
    except Exception as e:
        print(f"❌ Error validating Task model: {e}")
        return False

def validate_healthz_endpoint():
    """Validate /healthz endpoint implementation."""
    print("\n🔍 Validating /healthz endpoint...")
    try:
        from services.orchestrator.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/healthz")

        if response.status_code != 200:
            print(f"❌ /healthz returned status {response.status_code}")
            return False

        data = response.json()
        if data.get("status") != "ok":
            print(f"❌ /healthz returned unexpected data: {data}")
            return False

        print("✅ /healthz endpoint working correctly")
        return True
    except Exception as e:
        print(f"❌ Error validating /healthz endpoint: {e}")
        return False

def validate_task_endpoints():
    """Validate task-related endpoints."""
    print("\n🔍 Validating task endpoints...")
    try:
        from services.orchestrator.main import app
        from fastapi.testclient import TestClient
        from services.orchestrator.auth import pwd_context
        from services.orchestrator.database import SessionLocal

        client = TestClient(app)

        # Create test user and get token
        with SessionLocal() as db:
            # Clean up any existing test user
            db.execute("DELETE FROM users WHERE username = 'testuser'")
            db.commit()

            # Create test user
            user_data = {
                'id': 'test-user-id',
                'username': 'testuser',
                'email': 'test@example.com',
                'password_hash': pwd_context.hash('testpass123'),
                'role': 'admin'
            }
            db.execute("""
                INSERT INTO users (id, username, email, password_hash, role)
                VALUES (:id, :username, :email, :password_hash, :role)
            """, user_data)
            db.commit()

        # Login to get token
        login_response = client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
            return False

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test POST /collab/tasks
        task_data = {
            "title": "Test Task",
            "description": "A test task"
        }
        create_response = client.post("/api/v1/collab/tasks", json=task_data, headers=headers)

        if create_response.status_code != 201:
            print(f"❌ POST /collab/tasks failed: {create_response.status_code} - {create_response.text}")
            return False

        # Check ETag header
        if "ETag" not in create_response.headers:
            print("❌ POST /collab/tasks missing ETag header")
            return False

        # Check Location header
        if "Location" not in create_response.headers:
            print("❌ POST /collab/tasks missing Location header")
            return False

        task_id = create_response.json()["id"]

        # Test GET /collab/state/tasks
        list_response = client.get("/api/v1/collab/state/tasks", headers=headers)

        if list_response.status_code != 200:
            print(f"❌ GET /collab/state/tasks failed: {list_response.status_code} - {list_response.text}")
            return False

        # Check ETag header
        if "ETag" not in list_response.headers:
            print("❌ GET /collab/state/tasks missing ETag header")
            return False

        # Check response structure
        data = list_response.json()
        if data.get("kind") != "tasks":
            print(f"❌ GET /collab/state/tasks wrong kind: {data.get('kind')}")
            return False

        # Check our task is in the list
        task_ids = [task["id"] for task in data.get("items", [])]
        if task_id not in task_ids:
            print(f"❌ Created task {task_id} not found in list")
            return False

        # Test conditional GET with If-None-Match
        etag = list_response.headers["ETag"]
        conditional_response = client.get(
            "/api/v1/collab/state/tasks",
            headers={**headers, "If-None-Match": etag}
        )

        if conditional_response.status_code != 304:
            print(f"❌ Conditional GET failed: {conditional_response.status_code}")
            return False

        print("✅ Task endpoints working correctly")
        return True
    except Exception as e:
        print(f"❌ Error validating task endpoints: {e}")
        return False

def validate_tests():
    """Validate that all tests are present and can run."""
    print("\n🔍 Validating test suite...")
    try:
        test_file = project_root / "services" / "orchestrator" / "tests" / "test_backend_steel_thread.py"

        if not test_file.exists():
            print("❌ test_backend_steel_thread.py not found")
            return False

        # Check for required test classes
        content = test_file.read_text()
        required_classes = [
            "TestHealthzEndpoint",
            "TestCreateTaskEndpoint",
            "TestListTasksEndpoint",
            "TestEndpointIntegration",
            "TestErrorHandling"
        ]

        missing_classes = []
        for cls in required_classes:
            if f"class {cls}" not in content:
                missing_classes.append(cls)

        if missing_classes:
            print(f"❌ Missing test classes: {missing_classes}")
            return False

        print("✅ All required tests are present")
        return True
    except Exception as e:
        print(f"❌ Error validating tests: {e}")
        return False

def validate_security():
    """Validate security measures."""
    print("\n🔍 Validating security measures...")
    try:
        from services.orchestrator.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Test without authentication
        response = client.post("/api/v1/collab/tasks", json={"title": "Test"})
        if response.status_code != 401:
            print(f"❌ Unauthenticated request should return 401, got {response.status_code}")
            return False

        response = client.get("/api/v1/collab/state/tasks")
        if response.status_code != 401:
            print(f"❌ Unauthenticated request should return 401, got {response.status_code}")
            return False

        print("✅ Authentication properly enforced")
        return True
    except Exception as e:
        print(f"❌ Error validating security: {e}")
        return False

def main():
    """Run all validations."""
    print("🚀 Starting Backend Steel Thread Validation\n")

    validations = [
        validate_models,
        validate_healthz_endpoint,
        validate_task_endpoints,
        validate_tests,
        validate_security
    ]

    results = []
    for validation in validations:
        results.append(validation())

    print("\n" + "="*60)
    print("📊 VALIDATION SUMMARY")
    print("="*60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("Backend Steel Thread implementation is complete and working.")
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED!")
        print("Please review and fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())