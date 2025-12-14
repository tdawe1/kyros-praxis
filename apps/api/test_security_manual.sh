#!/bin/bash
# Manual Security Testing Script
# Tests all Phase 3 security fixes

set -e

API_URL="http://localhost:8001"

echo "============================================"
echo "SECURITY TEST SUITE - Phase 3"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

# Test function
test_endpoint() {
    local name="$1"
    local expected_status="$2"
    local method="$3"
    local endpoint="$4"
    local headers="$5"
    local data="$6"
    
    echo -n "TEST: $name ... "
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_URL$endpoint" \
            $headers \
            -H "Content-Type: application/json" \
            -d "$data")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_URL$endpoint" \
            $headers)
    fi
    
    status=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}PASS${NC} (HTTP $status)"
        ((pass_count++))
    else
        echo -e "${RED}FAIL${NC} (Expected $expected_status, got $status)"
        echo "Response: $body"
        ((fail_count++))
    fi
}

echo "=== PHASE 1: Unauthenticated Requests (should all return 401) ==="
echo ""

test_endpoint "Project update without auth" "401" "PATCH" "/projects/test-id" "" '{"name":"Hacked"}'
test_endpoint "Project delete without auth" "401" "DELETE" "/projects/test-id" "" ""
test_endpoint "Run retrieval without auth" "401" "GET" "/crews/runs/test-run" "" ""
test_endpoint "Run cancellation without auth" "401" "POST" "/crews/runs/test-run/cancel" "" ""
test_endpoint "Workflow generate without auth" "401" "POST" "/projects/test-id/generate" "" '{"prompt":"test"}'
test_endpoint "Workflow approve without auth" "401" "POST" "/projects/test-id/approve" "" '{"approved":true,"specification":{}}'
test_endpoint "Workflow regenerate without auth" "401" "POST" "/projects/test-id/regenerate" "" '{"refinement_notes":"test"}'
test_endpoint "Memory set without auth" "401" "POST" "/memory/set" "" '{"project_id":"test","key":"k","value":"v"}'
test_endpoint "Memory get without auth" "401" "POST" "/memory/get" "" '{"project_id":"test","key":"k"}'
test_endpoint "Batch runs without auth" "401" "POST" "/batch/runs" "" '{"project_id":"test","tasks":[]}'

echo ""
echo "=== PHASE 2: Authenticated Requests ===" 
echo ""

# Register user
echo -n "Registering test user ... "
register_response=$(curl -s -X POST "$API_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"username":"sectest","email":"sectest@test.com","password":"SecTest123!"}')

if echo "$register_response" | grep -q "sectest@test.com"; then
    echo -e "${GREEN}PASS${NC}"
    ((pass_count++))
else
    echo -e "${YELLOW}SKIP${NC} (user may already exist)"
fi

# Login
echo -n "Login and get token ... "
login_response=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"sectest@test.com","password":"SecTest123!"}')

TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((pass_count++))
else
    echo -e "${RED}FAIL${NC}"
    echo "Login response: $login_response"
    ((fail_count++))
    exit 1
fi

# Authenticated tests
AUTH_HEADER="-H \"Authorization: Bearer $TOKEN\""

echo ""
test_endpoint "Create project with auth" "201" "POST" "/projects" "$AUTH_HEADER" '{"name":"Test Project","description":"Test"}'

# Get project ID
projects_response=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/projects")
PROJECT_ID=$(echo "$projects_response" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -n "$PROJECT_ID" ]; then
    echo "Project created: $PROJECT_ID"
    test_endpoint "Update own project" "200" "PATCH" "/projects/$PROJECT_ID" "$AUTH_HEADER" '{"name":"Updated"}'
    test_endpoint "Get project dashboard" "200" "GET" "/projects/$PROJECT_ID/dashboard" "$AUTH_HEADER" ""
    test_endpoint "Create task" "201" "POST" "/projects/$PROJECT_ID/tasks" "$AUTH_HEADER" '{"title":"Test Task","description":"Test","priority":"P1"}'
else
    echo -e "${YELLOW}SKIP${NC} remaining tests (no project ID)"
fi

echo ""
test_endpoint "Create crew run with auth" "200" "POST" "/crews/runs" "$AUTH_HEADER" '{"crew_id":"test","input":{}}'

echo ""
echo "============================================"
echo "RESULTS"
echo "============================================"
echo -e "${GREEN}Passed: $pass_count${NC}"
echo -e "${RED}Failed: $fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    exit 1
fi
