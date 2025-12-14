#!/usr/bin/env python3
"""
Test script to verify database connection and model operations.
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from sqlalchemy.orm import Session
from models import Base, Job, Event, Task, User
from database import engine, SessionLocal, get_db
import uuid
from datetime import datetime

def test_database_connection():
    """Test basic database connection."""
    print("Testing database connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✅ Database connection successful: {result.scalar()}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_create_tables():
    """Test table creation."""
    print("\nTesting table creation...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return False

def test_user_model():
    """Test User model operations."""
    print("\nTesting User model...")
    try:
        db = SessionLocal()

        # Create a test user
        test_user = User(
            id=str(uuid.uuid4()),
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeZeUfkZMBs9kYZP6",  # 'password' hashed
            active=1,
            role="user"
        )

        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        # Query the user
        retrieved_user = db.query(User).filter(User.username == "testuser").first()
        if retrieved_user:
            print(f"✅ User created and retrieved successfully: {retrieved_user.username}")
        else:
            print("❌ Failed to retrieve user")
            return False

        # Clean up
        db.delete(test_user)
        db.commit()
        db.close()

        return True
    except Exception as e:
        print(f"❌ User model test failed: {e}")
        return False

def test_job_model():
    """Test Job model operations."""
    print("\nTesting Job model...")
    try:
        db = SessionLocal()

        # Create a test job
        test_job = Job(
            id=str(uuid.uuid4()),
            name="Test Job",
            description="A test job for verification",
            status="pending",
            priority=5,
            metadata={"test": True}
        )

        db.add(test_job)
        db.commit()
        db.refresh(test_job)

        # Query the job
        retrieved_job = db.query(Job).filter(Job.name == "Test Job").first()
        if retrieved_job:
            print(f"✅ Job created and retrieved successfully: {retrieved_job.name}")
        else:
            print("❌ Failed to retrieve job")
            return False

        # Clean up
        db.delete(test_job)
        db.commit()
        db.close()

        return True
    except Exception as e:
        print(f"❌ Job model test failed: {e}")
        return False

def test_event_model():
    """Test Event model operations."""
    print("\nTesting Event model...")
    try:
        db = SessionLocal()

        # Create a test event
        test_event = Event(
            id=str(uuid.uuid4()),
            type="test.event",
            payload={"message": "Test event"}
        )

        db.add(test_event)
        db.commit()
        db.refresh(test_event)

        # Query the event
        retrieved_event = db.query(Event).filter(Event.type == "test.event").first()
        if retrieved_event:
            print(f"✅ Event created and retrieved successfully: {retrieved_event.type}")
        else:
            print("❌ Failed to retrieve event")
            return False

        # Clean up
        db.delete(test_event)
        db.commit()
        db.close()

        return True
    except Exception as e:
        print(f"❌ Event model test failed: {e}")
        return False

def test_get_db_dependency():
    """Test the get_db dependency function."""
    print("\nTesting get_db dependency...")
    try:
        # This would normally be used by FastAPI, but we can test it directly
        db = next(get_db())
        if isinstance(db, Session):
            print("✅ get_db dependency working correctly")
            db.close()
            return True
        else:
            print("❌ get_db did not return a Session object")
            return False
    except Exception as e:
        print(f"❌ get_db dependency test failed: {e}")
        return False

def main():
    """Run all database tests."""
    print("=== Database Testing Suite ===\n")

    tests = [
        test_database_connection,
        test_create_tables,
        test_user_model,
        test_job_model,
        test_event_model,
        test_get_db_dependency
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n=== Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("🎉 All database tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)