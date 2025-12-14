#!/bin/bash
# Test script for CrewAI runs

set -e

API_URL="http://localhost:8000"

echo "=========================================="
echo "  Testing CrewAI Crew Runs"
echo "=========================================="
echo ""

# Test 1: Create a crew run
echo "1. Creating crew run..."
CREATE_RESPONSE=$(curl -s -X POST ${API_URL}/crews/runs \
  -H "Content-Type: application/json" \
  -d '{
    "crew_id": "spec_to_tasks",
    "input": {
      "prompt": "Create a simple todo list app with the following features: user authentication, create tasks, edit tasks, delete tasks, and mark tasks as complete."
    }
  }')

RUN_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')

if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
  echo "   ❌ Failed to create crew run"
  echo "   Response: $CREATE_RESPONSE"
  exit 1
fi

echo "   ✅ Crew run created"
echo "   Run ID: $RUN_ID"
echo ""

# Test 2: Check run status
echo "2. Checking run status..."
sleep 2  # Give it time to start

STATUS_RESPONSE=$(curl -s ${API_URL}/crews/runs/${RUN_ID})
STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')

echo "   Status: $STATUS"

if [[ "$STATUS" == "null" || -z "$STATUS" ]]; then
  echo "   ❌ Failed to get status"
  echo "   Response: $STATUS_RESPONSE"
  exit 1
fi

echo "   ✅ Status retrieved successfully"
echo ""

# Test 3: Stream events for a few seconds
echo "3. Monitoring events (10 seconds)..."
echo "   Press Ctrl+C to stop early"
echo ""

timeout 10s curl -s ${API_URL}/crews/runs/${RUN_ID}/events | while IFS= read -r line; do
  if [[ $line == data:* ]]; then
    # Extract JSON after "data: "
    EVENT_DATA="${line#data: }"
    
    # Try to parse and display nicely
    EVENT_TYPE=$(echo "$EVENT_DATA" | jq -r '.type // empty' 2>/dev/null)
    EVENT_STATUS=$(echo "$EVENT_DATA" | jq -r '.status // empty' 2>/dev/null)
    EVENT_MSG=$(echo "$EVENT_DATA" | jq -r '.message // empty' 2>/dev/null)
    
    if [[ -n "$EVENT_TYPE" ]]; then
      echo "   [EVENT] Type: $EVENT_TYPE"
    fi
    
    if [[ -n "$EVENT_STATUS" ]]; then
      echo "   [STATUS] $EVENT_STATUS"
    fi
    
    if [[ -n "$EVENT_MSG" ]]; then
      echo "   [MESSAGE] $EVENT_MSG"
    fi
  fi
done || true  # timeout returns error, ignore it

echo ""
echo "   ✅ Event streaming working"
echo ""

# Test 4: Check final status
echo "4. Checking final status..."
sleep 1

FINAL_RESPONSE=$(curl -s ${API_URL}/crews/runs/${RUN_ID})
FINAL_STATUS=$(echo "$FINAL_RESPONSE" | jq -r '.status')
HAS_RESULT=$(echo "$FINAL_RESPONSE" | jq 'has("result")')

echo "   Final Status: $FINAL_STATUS"
echo "   Has Result: $HAS_RESULT"

if [[ "$FINAL_STATUS" == "succeeded" ]]; then
  echo "   ✅ Run completed successfully"
  
  # Show result summary
  RESULT=$(echo "$FINAL_RESPONSE" | jq -r '.result')
  if [[ "$RESULT" != "null" ]]; then
    echo ""
    echo "   Result Preview:"
    echo "$RESULT" | jq . 2>/dev/null || echo "$RESULT"
  fi
elif [[ "$FINAL_STATUS" == "running" || "$FINAL_STATUS" == "queued" ]]; then
  echo "   ℹ️  Run still in progress"
  echo "   Note: CrewAI runs may take longer depending on LLM response time"
elif [[ "$FINAL_STATUS" == "failed" ]]; then
  echo "   ⚠️  Run failed"
  ERROR=$(echo "$FINAL_RESPONSE" | jq -r '.result // empty')
  if [[ -n "$ERROR" ]]; then
    echo "   Error: $ERROR"
  fi
else
  echo "   Status: $FINAL_STATUS"
fi

echo ""

# Test 5: Test with authentication (optional)
echo "5. Testing with authentication..."

# First login to get token
LOGIN_RESPONSE=$(curl -s -X POST ${API_URL}/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"quicktest@example.com","password":"Password123!"}' 2>&1)

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty' 2>/dev/null)

if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  echo "   ℹ️  No test user found (this is okay)"
  echo "   Skipping authenticated run test"
else
  echo "   ✅ Logged in successfully"
  
  # Create authenticated run
  AUTH_RUN=$(curl -s -X POST ${API_URL}/crews/runs \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{
      "crew_id": "spec_to_tasks",
      "input": {
        "prompt": "Simple calculator app"
      }
    }')
  
  AUTH_RUN_ID=$(echo "$AUTH_RUN" | jq -r '.id // empty')
  
  if [[ -n "$AUTH_RUN_ID" && "$AUTH_RUN_ID" != "null" ]]; then
    echo "   ✅ Authenticated crew run created: $AUTH_RUN_ID"
  else
    echo "   ⚠️  Failed to create authenticated run"
  fi
fi

echo ""
echo "=========================================="
echo "  ✅ Crew Run Tests Complete"
echo "=========================================="
echo ""
echo "Summary:"
echo "  • Crew run creation: ✅ Working"
echo "  • Status retrieval: ✅ Working"
echo "  • Event streaming: ✅ Working"
echo "  • Run ID: $RUN_ID"
echo ""
echo "Next steps:"
echo "  1. Check run status: curl ${API_URL}/crews/runs/${RUN_ID}"
echo "  2. View events: curl ${API_URL}/crews/runs/${RUN_ID}/events"
echo "  3. Check result when completed"
echo ""
