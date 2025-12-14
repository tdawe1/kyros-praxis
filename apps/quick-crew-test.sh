#!/bin/bash
# Quick crew run test (no streaming, just basic verification)

API_URL="http://localhost:8000"

echo "Creating a quick crew run..."

# Create run
RESPONSE=$(curl -s -X POST ${API_URL}/crews/runs \
  -H "Content-Type: application/json" \
  -d '{
    "crew_id": "spec_to_tasks",
    "input": {
      "prompt": "Build a simple weather app"
    }
  }')

RUN_ID=$(echo "$RESPONSE" | jq -r '.id')

if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
  echo "❌ Failed to create crew run"
  echo "Response: $RESPONSE"
  exit 1
fi

echo "✅ Crew run created: $RUN_ID"
echo ""
echo "Status: $(echo "$RESPONSE" | jq -r '.status')"
echo ""
echo "Check status with:"
echo "  curl ${API_URL}/crews/runs/${RUN_ID}"
echo ""
echo "Stream events with:"
echo "  curl ${API_URL}/crews/runs/${RUN_ID}/events"
echo ""
echo "Or view in browser:"
echo "  http://localhost:8000/docs"
