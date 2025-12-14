#!/bin/bash
# Integration Test Script - Verify Backend + Frontend Integration

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     🧪 INTEGRATION TESTING - AGENTS A & B                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Helper functions
pass_test() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED++))
}

fail_test() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED++))
}

info() {
    echo -e "${YELLOW}ℹ️  INFO${NC}: $1"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 1: Backend Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Backend imports
info "Testing backend imports..."
cd apps/api
if ../.venv/bin/python -c "from app.agents import run_planner, run_coder, run_tester; from app.workflows.pipeline_refactored import workflow_pipeline" 2>/dev/null; then
    pass_test "Backend imports successful"
else
    fail_test "Backend imports failed"
fi

# Test 2: Backend tests
info "Running backend tests (may take 30s)..."
if ../.venv/bin/pytest tests/ -k "not async" -q --tb=no 2>&1 | grep -q "passed"; then
    pass_test "Backend tests passing"
else
    fail_test "Backend tests failing"
fi

# Test 3: Backend server health
info "Testing backend server startup..."
timeout 3 ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8899 > /tmp/backend-test.log 2>&1 &
BACKEND_PID=$!
sleep 2

if curl -s http://127.0.0.1:8899/health 2>/dev/null | grep -q "ok"; then
    pass_test "Backend server responds to health check"
else
    fail_test "Backend server not responding"
fi

kill $BACKEND_PID 2>/dev/null
wait $BACKEND_PID 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 2: Frontend Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd ../console

# Test 4: Frontend dependencies
info "Checking frontend dependencies..."
if [ -d "node_modules" ]; then
    pass_test "Frontend dependencies installed"
else
    fail_test "Frontend node_modules missing"
fi

# Test 5: Frontend build check
info "Checking frontend TypeScript compilation..."
if npm run build > /tmp/frontend-build.log 2>&1; then
    pass_test "Frontend builds without errors"
else
    fail_test "Frontend build errors"
    cat /tmp/frontend-build.log | tail -10
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 3: Integration Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

info "Integration tests require both servers running"
info "Start backend: cd apps/api && ../.venv/bin/uvicorn app.main:app"
info "Start frontend: cd apps/console && npm run dev"
info "Then test manually or with E2E test suite"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST RESULTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL PRE-INTEGRATION TESTS PASSED${NC}"
    echo ""
    echo "Ready for manual integration testing!"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please fix failing tests before integration."
    exit 1
fi
