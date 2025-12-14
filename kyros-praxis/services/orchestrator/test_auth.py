#!/usr/bin/env python3
"""
Test script to verify authentication functions.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from auth import (
    pwd_context,
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    authenticate_user,
    create_user,
    get_user_by_username,
    get_user,
    JWT_ISSUER,
    JWT_AUDIENCE,
    SECRET_KEY,
    ALGORITHM
)
from models import User
from database import SessionLocal
import uuid
import jwt

def test_password_functions():
    """Test password hashing and verification."""
    print("Testing password functions...")
    try:
        # Test password hashing
        password = "testpassword123"
        hashed = get_password_hash(password)
        print(f"✅ Password hashed successfully")

        # Test password verification
        is_valid = verify_password(password, hashed)
        if is_valid:
            print("✅ Password verification successful")
        else:
            print("❌ Password verification failed")
            return False

        # Test wrong password
        is_valid_wrong = verify_password("wrongpassword", hashed)
        if not is_valid_wrong:
            print("✅ Wrong password correctly rejected")
        else:
            print("❌ Wrong password incorrectly accepted")
            return False

        return True
    except Exception as e:
        print(f"❌ Password functions test failed: {e}")
        return False

def test_jwt_functions():
    """Test JWT token creation and verification."""
    print("\nTesting JWT functions...")
    try:
        # Create test data
        test_data = {
            "sub": "testuser",
            "username": "testuser",
            "role": "user"
        }

        # Create access token
        token = create_access_token(data=test_data, expires_delta=timedelta(minutes=30))
        print(f"✅ Access token created successfully")

        # Verify token
        payload = verify_token(token)
        if payload and payload.get("sub") == "testuser":
            print("✅ Token verification successful")
        else:
            print("❌ Token verification failed")
            return False

        # Test expired token
        expired_token = create_access_token(data=test_data, expires_delta=timedelta(seconds=-1))
        try:
            verify_token(expired_token)
            print("❌ Expired token incorrectly accepted")
            return False
        except Exception:
            print("✅ Expired token correctly rejected")

        # Test invalid token
        try:
            verify_token("invalid.token.here")
            print("❌ Invalid token incorrectly accepted")
            return False
        except Exception:
            print("✅ Invalid token correctly rejected")

        return True
    except Exception as e:
        print(f"❌ JWT functions test failed: {e}")
        return False

def test_user_authentication():
    """Test user authentication flow."""
    print("\nTesting user authentication...")
    try:
        db = SessionLocal()

        # Clean up any existing test user first
        existing_user = get_user(db, "auth_test_user")
        if existing_user:
            db.delete(existing_user)
            db.commit()

        # Create a test user
        test_user = User(
            id=str(uuid.uuid4()),
            username="auth_test_user",
            email="auth@example.com",
            password_hash=get_password_hash("testpass123"),
            active=1,
            role="user"
        )

        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        # Test successful authentication
        auth_user = authenticate_user(db, "auth_test_user", "testpass123")
        if auth_user and auth_user.username == "auth_test_user":
            print("✅ User authentication successful")
        else:
            print("❌ User authentication failed")
            return False

        # Test wrong password
        auth_user_wrong = authenticate_user(db, "auth_test_user", "wrongpass")
        if auth_user_wrong is False:
            print("✅ Wrong password correctly rejected")
        else:
            print("❌ Wrong password incorrectly accepted")
            return False

        # Test non-existent user
        auth_user_none = authenticate_user(db, "nonexistent", "anypassword")
        if auth_user_none is False:
            print("✅ Non-existent user correctly rejected")
        else:
            print("❌ Non-existent user incorrectly accepted")
            return False

        # Clean up
        db.delete(test_user)
        db.commit()
        db.close()

        return True
    except Exception as e:
        print(f"❌ User authentication test failed: {e}")
        return False

def test_user_crud():
    """Test user CRUD operations."""
    print("\nTesting user CRUD operations...")
    try:
        db = SessionLocal()

        # Create user
        user_data = {
            "username": "crud_test_user",
            "email": "crud@example.com",
            "password": "crudpass123",
            "role": "user"
        }
        created_user = create_user(db, user_data)
        if created_user and created_user.username == "crud_test_user":
            print("✅ User creation successful")
        else:
            print("❌ User creation failed")
            return False

        # Get user by username
        retrieved_user = get_user_by_username(db, "crud_test_user")
        if retrieved_user and retrieved_user.id == created_user.id:
            print("✅ User retrieval successful")
        else:
            print("❌ User retrieval failed")
            return False

        # Test duplicate username
        try:
            duplicate_user = create_user(db, user_data)
            print("❌ Duplicate username incorrectly allowed")
            return False
        except Exception:
            print("✅ Duplicate username correctly rejected")

        # Clean up
        db.delete(created_user)
        db.commit()
        db.close()

        return True
    except Exception as e:
        print(f"❌ User CRUD test failed: {e}")
        return False

def test_token_with_user_data():
    """Test token creation with full user data."""
    print("\nTesting token with user data...")
    try:
        db = SessionLocal()

        # Create a test user
        test_user = User(
            id=str(uuid.uuid4()),
            username="token_test_user",
            email="token@example.com",
            password_hash=get_password_hash("tokenpass123"),
            active=1,
            role="admin"
        )

        db.add(test_user)
        db.commit()

        # Create token with user data
        user_data = {
            "sub": test_user.username,
            "username": test_user.username,
            "role": test_user.role,
            "user_id": str(test_user.id)
        }
        token = create_access_token(data=user_data)
        print("✅ Token with user data created successfully")

        # Verify token contains expected data
        payload = verify_token(token)
        expected_claims = ["sub", "username", "role", "user_id", "exp", "iat", "iss", "aud"]
        for claim in expected_claims:
            if claim not in payload:
                print(f"❌ Missing claim in token: {claim}")
                return False

        print("✅ Token contains all expected claims")

        # Clean up
        db.delete(test_user)
        db.commit()
        db.close()

        return True
    except Exception as e:
        print(f"❌ Token with user data test failed: {e}")
        return False

def test_security_configuration():
    """Test security configuration values."""
    print("\nTesting security configuration...")
    try:
        # Check if required security values are set
        if not SECRET_KEY or len(SECRET_KEY) < 32:
            print("❌ SECRET_KEY is not set or too short")
            return False
        print("✅ SECRET_KEY is properly configured")

        if not JWT_ISSUER:
            print("❌ JWT_ISSUER is not set")
            return False
        print("✅ JWT_ISSUER is configured")

        if not JWT_AUDIENCE:
            print("❌ JWT_AUDIENCE is not set")
            return False
        print("✅ JWT_AUDIENCE is configured")

        if not ALGORITHM:
            print("❌ ALGORITHM is not set")
            return False
        print("✅ ALGORITHM is configured")

        return True
    except Exception as e:
        print(f"❌ Security configuration test failed: {e}")
        return False

def main():
    """Run all authentication tests."""
    print("=== Authentication Testing Suite ===\n")

    tests = [
        test_password_functions,
        test_jwt_functions,
        test_user_authentication,
        test_user_crud,
        test_token_with_user_data,
        test_security_configuration
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
        print("🎉 All authentication tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)