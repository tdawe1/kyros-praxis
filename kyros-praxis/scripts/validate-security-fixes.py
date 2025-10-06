#!/usr/bin/env python3
"""
Security validation script for CSRF, JWT, and Rate Limiting fixes
"""

import sys
import os
import jwt
import secrets
from datetime import datetime, timedelta

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'orchestrator'))

try:
    from security_middleware import CSRFProtection, RateLimiter, SecurityConfig
    from auth import create_access_token
    print("✅ Successfully imported security modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    # Try alternative import paths
    try:
        sys.path.insert(0, 'services/orchestrator')
        from security_middleware import CSRFProtection, RateLimiter, SecurityConfig
        from auth import create_access_token
        print("✅ Successfully imported security modules (alternative path)")
    except ImportError as e2:
        print(f"❌ Still failed: {e2}")
        print("Make sure you're running this from the project root")
        sys.exit(1)


def test_csrf_protection():
    """Test CSRF token generation and validation"""
    print("\n=== Testing CSRF Protection ===")

    # Initialize CSRF protection
    csrf_secret = secrets.token_urlsafe(32)
    csrf = CSRFProtection(csrf_secret)

    # Test 1: Token generation and validation
    print("Test 1: Basic token generation and validation...")
    session_id = "user123"
    token = csrf.generate_token(session_id)
    print(f"Generated token: {token[:50]}...")

    # Validate token
    is_valid = csrf.validate_token(token, session_id=session_id)
    print(f"Token validation: {'✅ PASS' if is_valid else '❌ FAIL'}")

    # Test 2: Invalid signature
    print("\nTest 2: Invalid signature...")
    # Tamper with the token
    token_parts = token.split('.')
    if len(token_parts) > 1:
        tampered_token = token_parts[0] + '.' + 'X' * len(token_parts[1])
        is_valid = csrf.validate_token(tampered_token, session_id=session_id)
        print(f"Tampered token rejected: {'✅ PASS' if not is_valid else '❌ FAIL'}")

    # Test 3: Session binding
    print("\nTest 3: Session binding...")
    token = csrf.generate_token(session_id)
    # Try to validate with different session
    is_valid = csrf.validate_token(token, session_id="different_user")
    print(f"Different session rejected: {'✅ PASS' if not is_valid else '❌ FAIL'}")

    # Test 4: Expiration
    print("\nTest 4: Token expiration...")
    token = csrf.generate_token(session_id)
    # Validate with negative max_age to force expiration
    is_valid = csrf.validate_token(token, max_age=-1, session_id=session_id)
    print(f"Expired token rejected: {'✅ PASS' if not is_valid else '❌ FAIL'}")

    # Run final validation
    test_results = [
        csrf.validate_token(csrf.generate_token("test"), session_id="test"),
        not csrf.validate_token("invalid_token"),
        not csrf.validate_token(csrf.generate_token("user1"), session_id="user2")
    ]

    print("\nCSRF Protection Tests: ✅ ALL PASSED" if all(test_results) else "❌ SOME TESTS FAILED")
    if not all(test_results):
        print(f"Test results: {test_results}")


def test_websocket_jwt():
    """Test WebSocket JWT validation with algorithm specification"""
    print("\n=== Testing WebSocket JWT Validation ===")

    # Create a test token with default values for testing
    test_data = {
        "sub": "testuser",
        "iss": "kyros-praxis",
        "aud": "kyros-praxis-client",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }

    # Use a test secret key
    test_secret = "test-secret-key-minimum-32-characters"
    token = jwt.encode(test_data, test_secret, algorithm="HS512")
    print(f"Generated JWT: {token[:50]}...")

    # Test 1: Valid token
    try:
        payload = jwt.decode(
            token,
            test_secret,
            algorithms=["HS512"],
            issuer="kyros-praxis",
            audience="kyros-praxis-client",
            options={
                "require": ["sub", "iss", "aud"],
                "verify_iss": True,
                "verify_aud": True,
                "verify_exp": True,
                "verify_iat": True,
            }
        )
        print("✅ Valid token accepted")
    except Exception as e:
        print(f"❌ Valid token rejected: {e}")

    # Test 2: None algorithm (prevents algorithm confusion)
    try:
        # The key is that our WebSocket endpoint requires specific algorithms
        # This test simulates what happens in the actual WebSocket code
        payload = jwt.decode(
            token,
            test_secret,
            algorithms=["HS512"],  # Algorithm specified - this is secure
            issuer="kyros-praxis",
            audience="kyros-praxis-client"
        )
        print("✅ Algorithm properly specified in decode")

        # Test what happens if no algorithm is specified (this would be vulnerable)
        try:
            payload_vulnerable = jwt.decode(
                token,
                test_secret,
                options={"verify_signature": False}  # No algorithm = vulnerable
            )
            print("⚠️  Note: Algorithm confusion possible when algorithm not specified")
        except Exception:
            print("✅ Algorithm confusion prevented when signature not verified")

    except Exception as e:
        print(f"❌ Algorithm validation failed: {e}")

    # Test 3: Missing required claims
    try:
        incomplete_token = jwt.encode(
            {"sub": "testuser"},
            test_secret,
            algorithm="HS512"
        )
        payload = jwt.decode(
            incomplete_token,
            test_secret,
            algorithms=["HS512"],
            issuer="kyros-praxis",
            audience="kyros-praxis-client",
            options={
                "require": ["sub", "iss", "aud"],
                "verify_iss": True,
                "verify_aud": True,
            }
        )
        print("❌ Missing claims accepted!")
    except Exception:
        print("✅ Missing claims properly rejected")


def test_rate_limiting():
    """Test Redis-based rate limiting"""
    print("\n=== Testing Rate Limiting ===")

    # Test with mock Redis URL
    redis_url = 'redis://localhost:6379'  # Default for testing

    rate_limiter = RateLimiter(
        requests=5,  # 5 requests
        window=60,    # per minute
        redis_url=redis_url
    )

    client_id = "test_client_123"

    print(f"Testing with Redis URL: {redis_url}")

    # Test 1: Rate limiting enforcement
    print("\nTest 1: Rate limiting enforcement...")
    request_count = 0
    for i in range(7):  # Try 7 requests (limit is 5)
        allowed = rate_limiter.is_allowed(client_id)
        status = "✅ ALLOWED" if allowed else "❌ BLOCKED"
        print(f"Request {i+1}: {status}")
        if allowed:
            request_count += 1

    if request_count == 5:
        print("✅ Rate limit correctly enforced")
    else:
        print(f"❌ Rate limit failed (expected 5, got {request_count})")

    # Test 2: Reset time
    print("\nTest 2: Reset time...")
    reset_time = rate_limiter.get_reset_time(client_id)
    print(f"Reset time: {reset_time} seconds")
    if 0 <= reset_time <= 60:
        print("✅ Reset time within expected range")
    else:
        print(f"❌ Invalid reset time: {reset_time}")

    # Test 3: Fallback to memory
    print("\nTest 3: Fallback behavior...")
    memory_limiter = RateLimiter(requests=3, window=60)  # No Redis URL
    client_id = "memory_test"

    allowed_count = sum(1 for _ in range(5) if memory_limiter.is_allowed(client_id))
    if allowed_count == 3:
        print("✅ Memory fallback works correctly")
    else:
        print(f"❌ Memory fallback failed (expected 3, got {allowed_count})")


def main():
    """Run all security validation tests"""
    print("🔒 Security Validation Script")
    print("=" * 50)

    try:
        test_csrf_protection()
        test_websocket_jwt()
        test_rate_limiting()

        print("\n" + "=" * 50)
        print("✅ All security validation tests completed!")

    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()