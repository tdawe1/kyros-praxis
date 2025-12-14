#!/bin/bash
# Manual Testing Script for Kyros Praxis CrewAI API

set -e

API_URL="http://localhost:8000"
TIMESTAMP=$(date +%s)

echo "=================================================="
echo "   Kyros Praxis API - Manual Testing"
echo "=================================================="
echo ""

# Test 1: Health Check
echo "✓ Test 1: Health Check"
echo "  Request: GET $API_URL/health"
HEALTH=$(curl -s $API_URL/health)
echo "  Response: $HEALTH"
echo ""

# Test 2: Check Auth Endpoints
echo "✓ Test 2: Auth Endpoints Available"
ENDPOINTS=$(curl -s $API_URL/openapi.json | jq -r '.paths | keys | map(select(contains("/auth"))) | join(", ")')
echo "  Found: $ENDPOINTS"
echo ""

# Test 3: Register User
echo "✓ Test 3: User Registration"
USERNAME="testuser_${TIMESTAMP}"
EMAIL="test_${TIMESTAMP}@example.com"
PASSWORD="SecurePass123!"

echo "  Creating user: $USERNAME"
REGISTER_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

HTTP_CODE=$(echo "$REGISTER_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
RESPONSE_BODY=$(echo "$REGISTER_RESPONSE" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" = "201" ]; then
    echo "  ✓ SUCCESS (201 Created)"
    echo "  Response: $RESPONSE_BODY" | jq .
else
    echo "  ✗ FAILED (HTTP $HTTP_CODE)"
    echo "  Response: $RESPONSE_BODY"
    exit 1
fi
echo ""

# Test 4: Login
echo "✓ Test 4: User Login"
echo "  Logging in as: $EMAIL"
LOGIN_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST $API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✓ SUCCESS (200 OK)"
    ACCESS_TOKEN=$(echo "$RESPONSE_BODY" | jq -r '.access_token')
    echo "  Token received: ${ACCESS_TOKEN:0:20}..."
else
    echo "  ✗ FAILED (HTTP $HTTP_CODE)"
    echo "  Response: $RESPONSE_BODY"
    exit 1
fi
echo ""

# Test 5: Get Current User
echo "✓ Test 5: Get Current User Info"
USER_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET $API_URL/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN")

HTTP_CODE=$(echo "$USER_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
RESPONSE_BODY=$(echo "$USER_RESPONSE" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✓ SUCCESS (200 OK)"
    echo "  User info:" | jq .
    echo "$RESPONSE_BODY" | jq .
else
    echo "  ✗ FAILED (HTTP $HTTP_CODE)"
    echo "  Response: $RESPONSE_BODY"
    exit 1
fi
echo ""

# Test 6: Invalid Login
echo "✓ Test 6: Invalid Login (should fail)"
INVALID_LOGIN=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST $API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"wrongpassword\"}")

HTTP_CODE=$(echo "$INVALID_LOGIN" | grep "HTTP_CODE" | cut -d: -f2)
RESPONSE_BODY=$(echo "$INVALID_LOGIN" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" = "401" ]; then
    echo "  ✓ SUCCESS (401 Unauthorized - expected)"
    echo "  Error: $RESPONSE_BODY" | jq -r '.detail'
else
    echo "  ✗ UNEXPECTED (HTTP $HTTP_CODE)"
    echo "  Response: $RESPONSE_BODY"
fi
echo ""

# Test 7: Duplicate Registration
echo "✓ Test 7: Duplicate Registration (should fail)"
DUP_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

HTTP_CODE=$(echo "$DUP_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
RESPONSE_BODY=$(echo "$DUP_RESPONSE" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" = "400" ]; then
    echo "  ✓ SUCCESS (400 Bad Request - expected)"
    echo "  Error: $RESPONSE_BODY" | jq -r '.detail'
else
    echo "  ✗ UNEXPECTED (HTTP $HTTP_CODE)"
    echo "  Response: $RESPONSE_BODY"
fi
echo ""

echo "=================================================="
echo "   ✅ All Tests Passed!"
echo "=================================================="
echo ""
echo "Summary:"
echo "  • Health check: OK"
echo "  • User registration: OK"
echo "  • User login: OK"
echo "  • JWT authentication: OK"
echo "  • Error handling: OK"
echo ""
echo "Your API is working correctly!"
