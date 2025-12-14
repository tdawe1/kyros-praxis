#!/bin/bash

# Test JWT Auth Flow with HttpOnly Cookies

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         🧪 TESTING JWT AUTH FLOW                             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Start the API server in background
echo "Starting API server..."
mkdir -p .tmp
../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 > .tmp/kyros-api.log 2>&1 &
API_PID=$!
echo "API PID: $API_PID"
sleep 3

# Check if server is running
if ! curl -s http://localhost:8001/health > /dev/null; then
    echo "❌ API server failed to start"
    echo "Log:"
    sed -n '1,200p' .tmp/kyros-api.log
    kill $API_PID 2>/dev/null
    exit 1
fi

echo "✅ API server running"
echo ""

# Test 1: Register a test user
echo "1️⃣  Testing user registration..."
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser_'$(date +%s)'",
    "email": "test'$(date +%s)'@example.com",
    "password": "testpassword123"
  }')

if echo "$REGISTER_RESPONSE" | grep -q "id"; then
    echo "✅ User registered successfully"
    USER_EMAIL=$(echo "$REGISTER_RESPONSE" | grep -o '"email":"[^"]*"' | cut -d'"' -f4)
    echo "   Email: $USER_EMAIL"
else
    echo "⚠️  Registration failed (user may already exist)"
    USER_EMAIL="test@example.com"
fi
echo ""

# Test 2: Login and get cookies
echo "2️⃣  Testing login with cookie storage..."
LOGIN_RESPONSE=$(curl -s -c .tmp/cookies.txt -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$USER_EMAIL\",
    \"password\": \"testpassword123\"
  }")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login successful"
    echo "   Response includes: access_token, refresh_token"
    
    # Check cookies
    if [ -f .tmp/cookies.txt ]; then
        echo "   Cookies saved:"
        grep -E "(access_token|refresh_token)" .tmp/cookies.txt | awk '{print "     - " $6 " = " substr($7, 1, 20) "..."}'
    fi
else
    echo "❌ Login failed"
    echo "Response: $LOGIN_RESPONSE"
fi
echo ""

# Test 3: Access protected endpoint with cookie
echo "3️⃣  Testing protected endpoint with cookie..."
ME_RESPONSE=$(curl -s -b .tmp/cookies.txt http://localhost:8001/auth/me)

if echo "$ME_RESPONSE" | grep -q "email"; then
    echo "✅ Cookie-based auth working"
    echo "   User: $(echo "$ME_RESPONSE" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)"
else
    echo "❌ Cookie auth failed"
    echo "Response: $ME_RESPONSE"
fi
echo ""

# Test 4: Refresh tokens
echo "4️⃣  Testing token refresh..."
REFRESH_RESPONSE=$(curl -s -b .tmp/cookies.txt -c .tmp/cookies.txt \
  -X POST http://localhost:8001/auth/refresh)

if echo "$REFRESH_RESPONSE" | grep -q "access_token"; then
    echo "✅ Token refresh working"
    echo "   New tokens issued (rotation)"
else
    echo "❌ Token refresh failed"
    echo "Response: $REFRESH_RESPONSE"
fi
echo ""

# Test 5: Logout
echo "5️⃣  Testing logout..."
LOGOUT_RESPONSE=$(curl -s -b .tmp/cookies.txt -c .tmp/cookies.txt -X POST http://localhost:8001/auth/logout)

if echo "$LOGOUT_RESPONSE" | grep -q "Successfully logged out"; then
    echo "✅ Logout successful"
    
    # Try to access protected endpoint (should fail)
    ME_AFTER_LOGOUT=$(curl -s -b .tmp/cookies.txt http://localhost:8001/auth/me)
    if echo "$ME_AFTER_LOGOUT" | grep -q "detail"; then
        echo "✅ Cookies cleared - cannot access protected endpoint"
    else
        echo "⚠️  Still authenticated after logout (unexpected)"
    fi
else
    echo "❌ Logout failed"
    echo "Response: $LOGOUT_RESPONSE"
fi
echo ""

# Cleanup
echo "Cleaning up..."
kill $API_PID 2>/dev/null
rm -f .tmp/cookies.txt
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Auth flow test complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
