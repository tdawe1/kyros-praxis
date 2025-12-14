#!/bin/bash

# Comprehensive System Test
# Tests Phase 1 (Backend) and Phase 2 (Frontend)

set -e

API_BASE="http://localhost:8000"
CONSOLE_BASE="http://localhost:3000"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  Kyros Multi-Agent System Test Suite"
echo "=========================================="
echo ""

# Test counters
PASSED=0
FAILED=0
TOTAL=0

# Test helper
test_endpoint() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    local data="$4"
    local expected_code="${5:-200}"
    
    TOTAL=$((TOTAL + 1))
    echo -n "[$TOTAL] Testing $name... "
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null || echo -e "\n000")
    else
        response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo -e "\n000")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_code, got $http_code)"
        FAILED=$((FAILED + 1))
        if [ ! -z "$body" ]; then
            echo "  Response: ${body:0:100}"
        fi
        return 1
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Phase 1: Backend API Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Health Check
test_endpoint "API Health Check" "$API_BASE/health"

# Test 2: OpenAPI Docs
test_endpoint "OpenAPI Documentation" "$API_BASE/docs"

# Test 3: Create Project
echo ""
echo "Creating test project..."
PROJECT_RESPONSE=$(curl -s -X POST "$API_BASE/projects" \
    -H "Content-Type: application/json" \
    -d '{"name":"Test Project","description":"Automated test project"}' 2>/dev/null)

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4 | head -1)

if [ ! -z "$PROJECT_ID" ]; then
    echo -e "${GREEN}✓${NC} Project created: $PROJECT_ID"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗${NC} Failed to create project"
    echo "Response: $PROJECT_RESPONSE"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))

# Test 4: List Projects
test_endpoint "List Projects" "$API_BASE/projects"

# Test 5: Get Project
if [ ! -z "$PROJECT_ID" ]; then
    test_endpoint "Get Project by ID" "$API_BASE/projects/$PROJECT_ID"
fi

# Test 6: Create Task
echo ""
if [ ! -z "$PROJECT_ID" ]; then
    echo "Creating test task..."
    TASK_RESPONSE=$(curl -s -X POST "$API_BASE/projects/$PROJECT_ID/tasks" \
        -H "Content-Type: application/json" \
        -d '{"title":"Test Task","description":"Automated test task","priority":"P0"}' 2>/dev/null)
    
    TASK_ID=$(echo "$TASK_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4 | head -1)
    
    if [ ! -z "$TASK_ID" ]; then
        echo -e "${GREEN}✓${NC} Task created: $TASK_ID"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC} Failed to create task"
        FAILED=$((FAILED + 1))
    fi
    TOTAL=$((TOTAL + 1))
fi

# Test 7: List Tasks
if [ ! -z "$PROJECT_ID" ]; then
    test_endpoint "List Project Tasks" "$API_BASE/projects/$PROJECT_ID/tasks"
fi

# Test 8: Get Dashboard
if [ ! -z "$PROJECT_ID" ]; then
    test_endpoint "Get Project Dashboard" "$API_BASE/projects/$PROJECT_ID/dashboard"
fi

# Test 9: Shared Memory - Set
echo ""
if [ ! -z "$PROJECT_ID" ]; then
    echo "Testing shared memory..."
    MEMORY_RESPONSE=$(curl -s -X POST "$API_BASE/memory/set" \
        -H "Content-Type: application/json" \
        -d "{\"project_id\":\"$PROJECT_ID\",\"key\":\"test_key\",\"value\":{\"status\":\"testing\"}}" 2>/dev/null)
    
    if echo "$MEMORY_RESPONSE" | grep -q "ok"; then
        echo -e "${GREEN}✓${NC} Memory set successful"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC} Failed to set memory"
        FAILED=$((FAILED + 1))
    fi
    TOTAL=$((TOTAL + 1))
fi

# Test 10: Shared Memory - Get
if [ ! -z "$PROJECT_ID" ]; then
    MEMORY_GET=$(curl -s -X POST "$API_BASE/memory/get" \
        -H "Content-Type: application/json" \
        -d "{\"project_id\":\"$PROJECT_ID\",\"key\":\"test_key\"}" 2>/dev/null)
    
    if echo "$MEMORY_GET" | grep -q "testing"; then
        echo -e "${GREEN}✓${NC} Memory get successful"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC} Failed to get memory"
        FAILED=$((FAILED + 1))
    fi
    TOTAL=$((TOTAL + 1))
fi

# Test 11: Shared Memory - Get All
if [ ! -z "$PROJECT_ID" ]; then
    test_endpoint "Get All Memory" "$API_BASE/memory/$PROJECT_ID/all"
fi

# Test 12: Batch Runs
echo ""
if [ ! -z "$PROJECT_ID" ]; then
    echo "Testing batch run creation..."
    BATCH_RESPONSE=$(curl -s -X POST "$API_BASE/batch/runs" \
        -H "Content-Type: application/json" \
        -d "{
            \"project_id\":\"$PROJECT_ID\",
            \"tasks\":[
                {\"title\":\"Batch Task 1\",\"priority\":\"P0\"},
                {\"title\":\"Batch Task 2\",\"priority\":\"P1\"}
            ]
        }" 2>/dev/null)
    
    BATCH_ID=$(echo "$BATCH_RESPONSE" | grep -o '"batch_id":"[^"]*"' | cut -d'"' -f4)
    
    if [ ! -z "$BATCH_ID" ]; then
        echo -e "${GREEN}✓${NC} Batch run created: $BATCH_ID"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC} Failed to create batch run"
        echo "Response: ${BATCH_RESPONSE:0:200}"
        FAILED=$((FAILED + 1))
    fi
    TOTAL=$((TOTAL + 1))
fi

# Test 13: Crew Run
echo ""
echo "Testing crew run creation..."
CREW_RESPONSE=$(curl -s -X POST "$API_BASE/crews/runs" \
    -H "Content-Type: application/json" \
    -d '{"crew_id":"spec_to_tasks","input":{"prompt":"Test crew run"}}' 2>/dev/null)

CREW_RUN_ID=$(echo "$CREW_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4 | head -1)

if [ ! -z "$CREW_RUN_ID" ]; then
    echo -e "${GREEN}✓${NC} Crew run created: $CREW_RUN_ID"
    PASSED=$((PASSED + 1))
    
    # Test 14: Get Crew Run
    test_endpoint "Get Crew Run" "$API_BASE/crews/runs/$CREW_RUN_ID"
else
    echo -e "${RED}✗${NC} Failed to create crew run"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Phase 2: Frontend Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 15: Console Home Page
test_endpoint "Console Home Page" "$CONSOLE_BASE/"

# Test 16: Terminal Page
test_endpoint "Terminal Page" "$CONSOLE_BASE/terminal"

# Test 17: Check for Terminal Components
echo ""
echo "Checking Terminal page content..."
TERMINAL_HTML=$(curl -s "$CONSOLE_BASE/terminal" 2>/dev/null)

if echo "$TERMINAL_HTML" | grep -q "Kyros Terminal"; then
    echo -e "${GREEN}✓${NC} Terminal component loaded"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗${NC} Terminal component not found"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))

if echo "$TERMINAL_HTML" | grep -q "Ctrl+B"; then
    echo -e "${GREEN}✓${NC} Keyboard shortcuts displayed"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗${NC} Keyboard shortcuts not found"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))

if echo "$TERMINAL_HTML" | grep -q "Dashboard"; then
    echo -e "${GREEN}✓${NC} Dashboard component present"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗${NC} Dashboard component not found"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Integration Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 18: SSE Event Stream (just check connection)
if [ ! -z "$PROJECT_ID" ]; then
    echo "Testing SSE event stream..."
    timeout 2 curl -s -N "$API_BASE/memory/$PROJECT_ID/events" > /dev/null 2>&1
    EXIT_CODE=$?
    
    # Exit code 124 means timeout (good - connection works)
    # Exit code 0 means stream ended (also ok)
    if [ $EXIT_CODE -eq 124 ] || [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓${NC} SSE stream connection successful"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC} SSE stream connection failed"
        FAILED=$((FAILED + 1))
    fi
    TOTAL=$((TOTAL + 1))
fi

# Test 19: Database Connection
echo ""
echo "Testing database connection..."
DB_TEST=$(docker --host unix:///var/run/docker.sock exec kyros-api-db \
    psql -U kyros -d kyros_test -c "SELECT COUNT(*) FROM projects;" 2>/dev/null | grep -o '[0-9]' | head -1)

if [ ! -z "$DB_TEST" ]; then
    echo -e "${GREEN}✓${NC} Database connection successful (found $DB_TEST projects)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗${NC} Database connection failed"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))

# Test 20: Check all tables exist
echo ""
echo "Checking database schema..."
TABLES=$(docker --host unix:///var/run/docker.sock exec kyros-api-db \
    psql -U kyros -d kyros_test -c "\dt" 2>/dev/null)

REQUIRED_TABLES=("projects" "tasks" "shared_memory" "memory_events" "workflow_stages" "critic_feedback" "artifacts")

for table in "${REQUIRED_TABLES[@]}"; do
    TOTAL=$((TOTAL + 1))
    if echo "$TABLES" | grep -q "$table"; then
        echo -e "${GREEN}✓${NC} Table exists: $table"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC} Table missing: $table"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED/$TOTAL)*100}")

echo "Total Tests: $TOTAL"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "Success Rate: $SUCCESS_RATE%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ ALL TESTS PASSED SUCCESSFULLY  ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${YELLOW}╔════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠ SOME TESTS FAILED              ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════╝${NC}"
    exit 1
fi
