#!/usr/bin/env python3
"""
Simple test script for Jobs API endpoints with direct user creation
"""
import asyncio
import httpx
import json
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

BASE_URL = "http://localhost:9000"
DATABASE_URL = "sqlite:///./services/orchestrator/orchestrator.db"

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_user():
    """Create a test user directly in the database"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Delete existing user if any
        db.execute(text("DELETE FROM users WHERE username = 'testuser'"))

        # Create new user
        password_hash = pwd_context.hash("testpass123")
        user_id = str(uuid.uuid4())

        db.execute(
            text("INSERT INTO users (id, username, email, password_hash, role, active, created_at) VALUES (:id, :username, :email, :password_hash, :role, :active, datetime('now'))"),
            {
                "id": user_id,
                "username": "testuser",
                "email": "test@example.com",
                "password_hash": password_hash,
                "role": "user",
                "active": 1
            }
        )

        db.commit()
        print(f"✅ Created test user: testuser")
        return True
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        return False
    finally:
        db.close()

async def test_jobs_api():
    """Test Jobs API endpoints"""
    # First create the test user
    if not create_test_user():
        return

    print("\n=== Testing Jobs API ===")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Login to get token
        response = await client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })

        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return

        token_data = response.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")
        print(f"Token: {token[:50]}...")

        # Test 1: Create a job
        print("\n1. Creating a job...")
        job_data = {
            "name": "Test Job",
            "description": "A test job for API validation",
            "priority": 5,
            "metadata": {"type": "test", "env": "dev"}
        }

        response = await client.post("/api/v1/jobs", json=job_data, headers=headers)
        if response.status_code == 201:
            job = response.json()
            job_id = job["id"]
            print(f"✅ Job created: {job_id}")
            print(f"   Name: {job['name']}")
            print(f"   Status: {job['status']}")
            print(f"   Priority: {job['priority']}")
        else:
            print(f"❌ Failed to create job: {response.status_code} - {response.text}")
            return

        # Test 2: Get the job
        print("\n2. Getting job details...")
        response = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
        if response.status_code == 200:
            job = response.json()
            print(f"✅ Job retrieved: {job['name']}")
            print(f"   Created at: {job['created_at']}")
            if job.get('ETag'):
                print(f"   ETag: {job['ETag']}")
        else:
            print(f"❌ Failed to get job: {response.status_code} - {response.text}")

        # Test 3: Update the job
        print("\n3. Updating job...")
        update_data = {
            "status": "running",
            "priority": 10
        }

        response = await client.put(f"/api/v1/jobs/{job_id}", json=update_data, headers=headers)
        if response.status_code == 200:
            job = response.json()
            print(f"✅ Job updated: {job['status']}")
            if job.get('started_at'):
                print(f"   Started at: {job['started_at']}")
        else:
            print(f"❌ Failed to update job: {response.status_code} - {response.text}")

        # Test 4: List jobs
        print("\n4. Listing jobs...")
        response = await client.get("/api/v1/jobs?size=5", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Jobs list: {data['total']} total jobs")
            for job in data['jobs'][:3]:  # Show first 3
                print(f"   - {job['name']} ({job['status']})")
        else:
            print(f"❌ Failed to list jobs: {response.status_code} - {response.text}")

        # Test 5: Get metrics
        print("\n5. Getting job metrics...")
        response = await client.get("/api/v1/jobs/metrics", headers=headers)
        if response.status_code == 200:
            metrics = response.json()
            print("✅ Job metrics:")
            for key, value in metrics.items():
                if value is not None:
                    print(f"   {key}: {value}")
        else:
            print(f"❌ Failed to get metrics: {response.status_code} - {response.text}")

        # Test 6: Delete the job
        print("\n6. Deleting job...")
        response = await client.delete(f"/api/v1/jobs/{job_id}", headers=headers)
        if response.status_code == 200:
            print("✅ Job deleted")

            # Verify deletion
            response = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
            if response.status_code == 404:
                print("✅ Job verified as deleted")
        else:
            print(f"❌ Failed to delete job: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(test_jobs_api())