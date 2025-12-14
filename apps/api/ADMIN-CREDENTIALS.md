# Admin Credentials

**⚠️ KEEP THIS FILE SECURE - DO NOT COMMIT TO GIT ⚠️**

## Admin Account

**Email**: `admin@kyros-praxis.dev`  
**Password**: `Admin123!`  
**Role**: `user` (can be upgraded to admin if needed)

*Note: Password was simplified for local testing.*

---

## Login Command

```bash
curl -X POST http://localhost:8001/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "admin@kyros-praxis.dev",
    "password": "AdminPass123!"
  }'
```

## Get Token (Save to Variable)

```bash
export ADMIN_TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@kyros-praxis.dev","password":"AdminPass123!"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "Token: ${ADMIN_TOKEN:0:30}..."
```

## Use Token for Requests

```bash
# Create project as admin
curl -X POST http://localhost:8001/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"name":"Admin Project","description":"Created by admin"}'

# List all projects
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8001/projects
```

---

## Create Additional Users

### Regular User
```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user1",
    "email": "user1@kyros-praxis.dev",
    "password": "User123!Pass"
  }'
```

### Make User Admin (via Database)
```bash
PGPASSWORD=kyros psql -h localhost -U kyros -d kyros -c \
  "UPDATE users SET role = 'admin' WHERE email = 'user1@kyros-praxis.dev';"
```

---

## Change Admin Password

```bash
# Login first
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@kyros-praxis.dev","password":"AdminPass123!"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# Change password (if endpoint exists)
curl -X POST http://localhost:8001/auth/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "old_password": "AdminPass123!",
    "new_password": "NewSecurePassword123!"
  }'
```

---

## Security Notes

1. **Change the default password** immediately in production
2. **Use strong passwords** (min 12 characters, mixed case, numbers, symbols)
3. **Never commit** this file to version control
4. **Rotate passwords** regularly (every 90 days recommended)
5. **Use environment variables** for credentials in scripts

---

## Testing Admin Access

```bash
# Get admin token
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@kyros-praxis.dev","password":"AdminPass123!"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# Get user info (verify admin role)
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8001/auth/me | jq .

# Expected output:
# {
#   "id": "...",
#   "username": "admin",
#   "email": "admin@kyros-praxis.dev",
#   "role": "admin",  <-- Should be "admin"
#   "active": true
# }
```

---

**Created**: January 2024  
**Last Updated**: January 2024
