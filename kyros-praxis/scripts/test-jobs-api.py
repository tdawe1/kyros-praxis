#!/usr/bin/env python3
"""
Test script for Jobs API endpoints
"""
import asyncio
import httpx
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

async def get_auth_token(client: httpx.AsyncClient) -> str:
    """Get authentication token"""
    # Create a test user first
    await client.post("/users", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    })

    # Login to get token
    response = await client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })

    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None

async def test_create_job():
    """Test job creation"""
    print("\n=== Testing Job Creation ===")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        token = await get_auth_token(client)
        if not token:
            print("❌ Failed to get auth token")
            return False

        headers = {"Authorization": f"Bearer {token}"}

        # Test cases
        test_jobs = [
            {
                "name": "Test Job 1",
                "description": "First test job",
                "priority": 1,
                "metadata": {"type": "test", "category": "unit"}
            },
            {
                "name": "Test Job 2",
                "priority": 5,
                "metadata": {"env": "production"}
            }
        ]

        for job_data in test_jobs:
            response = await client.post("/api/v1/jobs", json=job_data, headers=headers)
            if response.status_code == 201:
                job = response.json()
                print(f"✅ Created job: {job['id']} - {job['name']}")
            else:
                print(f"❌ Failed to create job: {response.status_code} - {response.text}")
                return False

        return True

async def test_get_jobs():
    """Test getting jobs list with pagination and filters"""
    print("\n=== Testing Get Jobs ===")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        token = await get_auth_token(client)
        if not token:
            print("❌ Failed to get auth token")
            return False

        headers = {"Authorization": f"Bearer {token}"}

        # Test basic pagination
        response = await client.get("/api/v1/jobs?page=1&size=5", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got jobs: {data['total']} total, page {data['page']}")
        else:
            print(f"❌ Failed to get jobs: {response.status_code} - {response.text}")
            return False

        # Test status filter
        response = await client.get("/api/v1/jobs?status=pending", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Filtered by status: {len(data['jobs'])} pending jobs")
        else:
            print(f"❌ Failed to filter by status: {response.status_code} - {response.text}")
            return False

        return True

async def test_update_job():
    """Test job updates"""
    print("\n=== Testing Job Updates ===")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        token = await get_auth_token(client)
        if not token:
            print("❌ Failed to get auth token")
            return False

        headers = {"Authorization": f"Bearer {token}"}

        # First create a job
        create_response = await client.post("/api/v1/jobs", json={
            "name": "Update Test Job",
            "description": "Will be updated",
            "priority": 3
        }, headers=headers)

        if create_response.status_code != 201:
            print("❌ Failed to create test job")
            return False

        job = create_response.json()
        job_id = job['id']

        # Update the job
        update_data = {
            "name": "Updated Job Name",
            "status": "running",
            "priority": 5
        }

        response = await client.put(f"/api/v1/jobs/{job_id}", json=update_data, headers=headers)
        if response.status_code == 200:
            updated_job = response.json()
            print(f"✅ Updated job: {updated_job['name']} - Status: {updated_job['status']}")
            if updated_job['started_at']:
                print(f"✅ Started at: {updated_job['started_at']}")
        else:
            print(f"❌ Failed to update job: {response.status_code} - {response.text}")
            return False

        return True

async def test_job_metrics():
    """Test job metrics endpoint"""
    print("\n=== Testing Job Metrics ===")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        token = await get_auth_token(client)
        if not token:
            print("❌ Failed to get auth token")
            return False

        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/v1/jobs/metrics", headers=headers)
        if response.status_code == 200:
            metrics = response.json()
            print(f"✅ Job Metrics:")
            print(f"   Total Jobs: {metrics['total_jobs']}")
            print(f"   Pending: {metrics['pending_jobs']}")
            print(f"   Running: {metrics['running_jobs']}")
            print(f"   Completed: {metrics['completed_jobs']}")
            print(f"   Failed: {metrics['failed_jobs']}")
            if metrics['average_completion_time']:
                print(f"   Avg Completion: {metrics['average_completion_time']:.2f}s")
        else:
            print(f"❌ Failed to get metrics: {response.status_code} - {response.text}")
            return False

        return True

async def test_delete_job():
    """Test job deletion"""
    print("\n=== Testing Job Deletion ===")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        token = await get_auth_token(client)
        if not token:
            print("❌ Failed to get auth token")
            return False

        headers = {"Authorization": f"Bearer {token}"}

        # Create a job to delete
        create_response = await client.post("/api/v1/jobs", json={
            "name": "Delete Test Job",
            "description": "Will be deleted"
        }, headers=headers)

        if create_response.status_code != 201:
            print("❌ Failed to create test job for deletion")
            return False

        job = create_response.json()
        job_id = job['id']

        # Delete the job
        response = await client.delete(f"/api/v1/jobs/{job_id}", headers=headers)
        if response.status_code == 200:
            print(f"✅ Deleted job: {job_id}")

            # Verify it's deleted
            get_response = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
            if get_response.status_code == 404:
                print("✅ Job verified as deleted")
            else:
                print("❌ Job still exists after deletion")
                return False
        else:
            print(f"❌ Failed to delete job: {response.status_code} - {response.text}")
            return False

        return True

async def test_etag_headers():
    """Test ETag headers on endpoints"""
    print("\n=== Testing ETag Headers ===")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        token = await get_auth_token(client)
        if not token:
            print("❌ Failed to get auth token")
            return False

        headers = {"Authorization": f"Bearer {token}"}

        # Test ETag on jobs list
        response = await client.get("/api/v1/jobs", headers=headers)
        if response.status_code == 200:
            etag = response.headers.get("ETag")
            if etag:
                print(f"✅ ETag on jobs list: {etag}")

                # Test conditional request
                headers["If-None-Match"] = etag
                response2 = await client.get("/api/v1/jobs", headers=headers)
                if response2.status_code == 304:
                    print("✅ Conditional request returned 304 Not Modified")
                else:
                    print(f"⚠️  Conditional request returned: {response2.status_code}")
            else:
                print("❌ No ETag header found")
        else:
            print(f"❌ Failed to get jobs: {response.status_code} - {response.text}")
            return False

        return True

async def main():
    """Run all tests"""
    print("🧪 Testing Jobs API Endpoints")
    print("=" * 50)

    # Check if server is running
    try:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/healthz")
            if response.status_code != 200:
                print("❌ Server is not healthy")
                return
    except httpx.ConnectError:
        print("❌ Cannot connect to server. Make sure it's running on localhost:8000")
        return

    print("✅ Server is healthy")

    # Run tests
    tests = [
        test_create_job,
        test_get_jobs,
        test_update_job,
        test_job_metrics,
        test_delete_job,
        test_etag_headers,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if await test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed!")

if __name__ == "__main__":
    asyncio.run(main())