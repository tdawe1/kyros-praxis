#!/usr/bin/env python3
"""
Direct test of Jobs API without auth first
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_jobs_no_auth():
    """Test Jobs API without authentication (should fail)"""
    print("=== Testing Jobs API without auth ===")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Try to create a job (should fail with 401)
        response = await client.post("/api/v1/jobs", json={
            "name": "Test Job",
            "description": "A test job",
            "priority": 1
        })
        print(f"Create job without auth: {response.status_code}")

        if response.status_code == 401:
            print("✅ Correctly requires authentication")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_jobs_no_auth())