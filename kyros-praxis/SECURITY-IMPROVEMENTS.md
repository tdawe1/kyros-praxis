# Security Improvements

This document outlines the security improvements made to the Kyros Praxis codebase.

## 1. Secrets Management

### .env Files
- Removed committed `.env` files that contained sensitive credentials
- Created `.env.example` files in the root directory and service directories
- Added `.env` to `.gitignore` to prevent accidental commits

### Environment Variables
The following environment variables are now required:

- `SECRET_KEY` - Cryptographically secure secret for JWT signing
- `NEXTAUTH_SECRET` - Secret for NextAuth session encryption
- `CSRF_SECRET` - Secret for CSRF token generation
- `POSTGRES_PASSWORD` - Database password
- `REDIS_PASSWORD` - Redis password (if applicable)
- `QDRANT_API_KEY` - Qdrant API key (if applicable)

## 2. JWT Implementation Fixes

### Centralized Configuration
- JWT settings are now centralized in `app/core/config.py`
- Uses `HS512` algorithm instead of `HS256` for stronger security
- Consistent issuer (`kyros-praxis`) and audience (`kyros-app`) claims

### Proper Claims
- JWT tokens now include all required claims:
  - `iss` (issuer)
  - `aud` (audience)
  - `exp` (expiration)
  - `iat` (issued at)
  - `sub` (subject)

### Error Handling
- Fixed null-guard issue that was causing 500 errors instead of 401
- Proper error handling for missing or invalid credentials

## 3. Authentication Improvements

### NextAuth
- Replaced dev-only authorize function with real authentication
- NextAuth now authenticates against the orchestrator API
- Tokens are properly stored and used in sessions
- Removed default secret fallback that was insecure

### WebSocket Authentication
- WebSocket connections now pass JWT tokens as query parameters
- Added token parameter to `useWebSocket` hook
- Backend will need to be updated to verify tokens from query parameters

## 4. Network Security

### HTTPS
- API client now uses HTTPS in production environments
- WebSocket connections should use `wss://` in production

### Pre-commit Hook
- Added pre-commit hook to prevent committing secrets
- Checks for common secret patterns in staged files
- Prevents committing `.env` files

## 5. Setup Instructions

1. Copy `.env.example` files to `.env` in each directory:
   ```bash
   cp .env.example .env
   cp services/orchestrator/.env.example services/orchestrator/.env
   cp services/console/.env.example services/console/.env
   ```

2. Fill in the values in each `.env` file with secure, unique values

3. Generate secure secrets using:
   ```bash
   openssl rand -hex 32  # 64-character hex string
   openssl rand -base64 32  # Base64 encoded
   ```

4. Install the pre-commit hook:
   ```bash
   ln -s ../../scripts/pre-commit-secret-check .git/hooks/pre-commit
   ```

## 6. Backend WebSocket Changes Needed

The backend WebSocket endpoint (`/ws`) will need to be updated to verify JWT tokens passed as query parameters:

```python
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    token: str = None  # Get token from query parameters
) -> None:
    # Verify token here
    if not token:
        await websocket.close(code=4000)
        return
        
    # Verify JWT token
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        # Extract user and continue with authentication
    except JWTError:
        await websocket.close(code=4001)
        return
    
    await websocket.accept()
    # ... rest of WebSocket logic
```