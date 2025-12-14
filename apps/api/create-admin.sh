#!/bin/bash
# Create Admin User Script

set -e

API_URL="http://localhost:8001"

echo "============================================"
echo "Create Admin User"
echo "============================================"
echo ""

# Default credentials (change if desired)
USERNAME="${1:-admin}"
# Use a valid domain for email validation (avoid .local/.localhost)
EMAIL="${2:-admin@kyros-praxis.dev}"
PASSWORD="${3:-Admin123!SecurePass}"

echo "Creating admin user..."
echo "  Username: $USERNAME"
echo "  Email: $EMAIL"
echo "  Password: $PASSWORD"
echo ""

# Register user
echo "Step 1: Registering user..."
REGISTER_RESPONSE=$(curl -s -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$USERNAME\",
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

# Determine if registration succeeded (response contains an id)
if echo "$REGISTER_RESPONSE" | grep -q '"id"'; then
  echo "✅ User registered successfully"
  USER_ID=$(echo "$REGISTER_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
  echo "  User ID: $USER_ID"
else
  echo "⚠️  Registration did not return an id (may already exist)"
  echo "    Response: $REGISTER_RESPONSE"
  echo "    Proceeding to login..."
fi

# Login to get token
echo ""
echo "Step 2: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST $API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed: $LOGIN_RESPONSE"
  echo "Attempting to reset password and retry login..."
  if [ -x "../.venv/bin/python" ] && [ -f "$(pwd)/reset-admin-password.py" ]; then
    ../.venv/bin/python reset-admin-password.py "$EMAIL" "$PASSWORD" || true
  else
    echo "⚠️  Could not run password reset helper; ensure Python venv exists."
  fi
  # Retry login
  LOGIN_RESPONSE=$(curl -s -X POST $API_URL/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
  TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
  if [ -z "$TOKEN" ]; then
    echo "❌ Login still failing: $LOGIN_RESPONSE"
    exit 1
  fi
fi

echo "✅ Login successful"
echo "  Token: ${TOKEN:0:30}..."

# Get user ID from token if we don't have it
if [ -z "$USER_ID" ]; then
    # Extract user info from /auth/me endpoint
    ME_RESPONSE=$(curl -s -X GET $API_URL/auth/me \
      -H "Authorization: Bearer $TOKEN")
    USER_ID=$(echo "$ME_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
fi

# Upgrade to admin role (requires direct database access)
echo ""
echo "Step 3: Upgrading to admin role..."
echo "  (This requires database access)"

# Try to update via database
if command -v psql &> /dev/null; then
    # Database credentials from .env
    DB_USER="kyros"
    DB_NAME="kyros"
    DB_HOST="localhost"
    
    SQL="UPDATE users SET role = 'admin' WHERE email = '$EMAIL';"
    
    if PGPASSWORD=kyros psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "$SQL" 2>/dev/null; then
        echo "✅ User upgraded to admin role"
    else
        echo "⚠️  Could not update role via database"
        echo "Manual step required:"
        echo "  psql -h localhost -U kyros -d kyros"
        echo "  UPDATE users SET role = 'admin' WHERE email = '$EMAIL';"
    fi
else
    echo "⚠️  psql not available"
    echo "Manual step required to upgrade to admin:"
    echo ""
    echo "  psql -h localhost -U kyros -d kyros"
    echo "  UPDATE users SET role = 'admin' WHERE email = '$EMAIL';"
fi

# Verify
echo ""
echo "Step 4: Verifying admin access..."
ME_RESPONSE=$(curl -s -X GET $API_URL/auth/me \
  -H "Authorization: Bearer $TOKEN")

ROLE=$(echo "$ME_RESPONSE" | grep -o '"role":"[^"]*' | cut -d'"' -f4)

if [ "$ROLE" = "admin" ]; then
    echo "✅ Admin user verified!"
else
    echo "⚠️  User role is: $ROLE (not admin yet)"
    echo "Run the manual database update above."
fi

echo ""
echo "============================================"
echo "Admin Credentials"
echo "============================================"
echo ""
echo "  Email:    $EMAIL"
echo "  Password: $PASSWORD"
echo "  Token:    $TOKEN"
echo ""
echo "Save these credentials securely!"
echo ""
echo "To login again:"
echo "  curl -X POST $API_URL/auth/login \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}'"
echo ""
