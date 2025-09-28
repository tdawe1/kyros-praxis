# MCP Security Implementation

This document describes the secure Model Context Protocol (MCP) implementation following the June 2025 OAuth Resource Server specification.

## Overview

The Kyros MCP servers now implement comprehensive security measures including:

- **OAuth 2.1 Resource Server** compliance
- **Bearer token validation** (Authorization: Bearer <token>)
- **API key authentication** (X-API-Key header)
- **Filesystem boundaries** to prevent unauthorized file access
- **PKCE support** for public clients
- **Resource indicators** (RFC 8707) for token audience restriction
- **Security audit logging** for compliance and monitoring

## Security Architecture

### OAuth Resource Server Pattern

Both `kyros-mcp` and `zen-mcp` servers act as OAuth 2.1 Resource Servers:

1. **Token Validation**: All requests must include either:
   - `Authorization: Bearer <jwt-token>` header (OAuth 2.1)
   - `X-API-Key: <api-key>` header (service-to-service)

2. **Protected Resource Metadata**: Available at `resources/oauth-protected-resource` endpoint

3. **Error Handling**: Invalid/expired tokens receive HTTP 401 responses with proper WWW-Authenticate headers

### Authentication Methods

#### Bearer Tokens (OAuth 2.1)
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Tokens must include standard JWT claims:
- `exp`: Expiration time
- `iss`: Issuer (configurable)
- `aud`: Audience (server-specific)
- `sub`: Subject (user ID)
- `scope`: Authorized scopes

#### API Keys (Service-to-Service)
```http
X-API-Key: your-service-api-key
```

For backend service communication and automated systems.

### Filesystem Security

File access is restricted to defined "roots" to prevent path traversal attacks:

```python
# Example allowed roots
allowed_roots = [
    "/opt/kyros/data",
    "/app/workspace", 
    "/tmp/kyros"
]
```

All file operations validate paths against these boundaries.

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# OAuth/JWT Settings
MCP_JWT_SECRET=your-super-secret-jwt-signing-key
MCP_REQUIRE_HTTPS=true

# API Keys
MCP_API_KEYS=service-key-1,service-key-2
QDRANT_API_KEY=your-qdrant-key
ZEN_API_KEYS=zen-admin-key

# Filesystem Security
KYROS_DATA_ROOT=/opt/kyros/data
ZEN_ROOT=/opt/kyros/zen

# Authorization Servers
KYROS_AUTH_SERVER=https://auth.kyros.ai/oauth
```

### Server Configuration

#### Kyros MCP Server
```python
# Secure configuration
MCP_SECURITY = create_mcp_security(
    server_name="kyros-mcp",
    jwt_secret=os.getenv("MCP_JWT_SECRET"),
    api_keys=[QDRANT_API_KEY] if QDRANT_API_KEY else [],
    allowed_roots=[
        "/opt/kyros/data",
        "/app",
        "/opt/kyros"
    ],
    authorization_servers=["https://auth.kyros.ai/oauth"],
    resource_uri="urn:kyros:mcp:kyros-mcp"
)
```

#### Zen MCP Server
```python
# Secure configuration
MCP_SECURITY = create_mcp_security(
    server_name="zen-mcp",
    jwt_secret=os.getenv("MCP_JWT_SECRET"),
    api_keys=os.getenv("ZEN_API_KEYS", "").split(","),
    allowed_roots=[
        str(ZEN_ROOT),
        str(STATE_DIR),
        str(CONTEXT_DIR)
    ],
    authorization_servers=["https://auth.kyros.ai/oauth"],
    resource_uri="urn:kyros:mcp:zen"
)
```

## Usage Examples

### Client Authentication

#### Using Bearer Token
```python
import json
import sys

# MCP request with Bearer token
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "kyros/runs",
        "arguments": {"action": "health"}
    },
    "headers": {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}

print(json.dumps(request))
```

#### Using API Key
```python
# MCP request with API key
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "zen/list_agents",
        "arguments": {}
    },
    "headers": {
        "X-API-Key": "your-service-api-key"
    }
}

print(json.dumps(request))
```

### Error Responses

Invalid authentication receives standardized error responses:

```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "error": {
        "code": 401,
        "message": "Authentication required",
        "data": {
            "www_authenticate": "Bearer realm=\"kyros-mcp\"",
            "supported_methods": ["bearer", "api_key"]
        }
    }
}
```

### OAuth Metadata Discovery

Clients can discover OAuth configuration:

```bash
# Request OAuth protected resource metadata
echo '{"jsonrpc":"2.0","id":1,"method":"resources/oauth-protected-resource"}' | python kyros-mcp/main.py
```

Response:
```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "metadata": {
            "resource": "urn:kyros:mcp:kyros-mcp",
            "authorization_servers": ["https://auth.kyros.ai/oauth"],
            "bearer_methods_supported": ["header"],
            "code_challenge_methods_supported": ["S256"],
            "grant_types_supported": ["authorization_code", "client_credentials"],
            "scopes_supported": ["read", "write", "admin"]
        }
    }
}
```

## Security Features

### 1. Authentication & Authorization
- ✅ OAuth 2.1 Resource Server compliance
- ✅ JWT Bearer token validation
- ✅ API key validation with constant-time comparison
- ✅ Scope-based authorization (read, write, admin)
- ✅ Token caching for performance

### 2. Attack Prevention
- ✅ Path traversal attack prevention
- ✅ Timing attack resistance
- ✅ Token mis-redemption protection (RFC 8707)
- ✅ HTTPS enforcement (configurable)
- ✅ Input validation and sanitization

### 3. Compliance & Monitoring
- ✅ Security audit logging
- ✅ PKCE support for public clients
- ✅ Standard error responses
- ✅ WWW-Authenticate headers
- ✅ Resource indicators support

### 4. Filesystem Security
- ✅ Configurable filesystem boundaries
- ✅ Path validation against allowed roots
- ✅ Prevention of directory traversal
- ✅ Safe file operations only

## Testing

Run the security test suite:

```bash
cd kyros-praxis/integrations
python test_mcp_security.py
```

Expected output:
```
✅ All MCP Security tests passed!

Security features implemented:
✓ OAuth 2.1 Resource Server compliance
✓ Bearer token validation (Authorization: Bearer <token>)
✓ API key validation (X-API-Key header)
✓ Filesystem boundaries and path validation
✓ PKCE support for public clients
✓ Resource indicators (RFC 8707) support
✓ .well-known/oauth-protected-resource metadata
✓ Security audit logging
✓ Standardized error responses with HTTP 401
✓ Protection against timing attacks
✓ Path traversal attack prevention
```

## Migration Guide

### From Insecure to Secure MCP

1. **Update Environment**: Configure authentication secrets and API keys
2. **Update Clients**: Add authentication headers to all requests
3. **Configure Boundaries**: Set allowed filesystem roots
4. **Test Authentication**: Verify all endpoints require proper auth
5. **Monitor Logs**: Check security audit logs for suspicious activity

### Breaking Changes

- ⚠️ **All requests now require authentication** (except `initialize`)
- ⚠️ **File operations restricted** to configured roots
- ⚠️ **API responses include security metadata**
- ⚠️ **Protocol version updated** to `2025-06-01`

## Production Deployment

### Required Environment Variables
```bash
MCP_JWT_SECRET=<cryptographically-secure-secret>
MCP_API_KEYS=<comma-separated-api-keys>
MCP_REQUIRE_HTTPS=true
KYROS_DATA_ROOT=<safe-data-directory>
ZEN_ROOT=<safe-zen-directory>
```

### Security Checklist
- [ ] Strong JWT secret (32+ random bytes)
- [ ] Unique API keys per service
- [ ] HTTPS enforcement enabled
- [ ] Filesystem roots properly configured
- [ ] Security audit logging enabled
- [ ] Regular token rotation implemented
- [ ] Monitor for failed authentication attempts

## Troubleshooting

### Common Issues

1. **401 Authentication Required**
   - Check Authorization header format
   - Verify API key is in MCP_API_KEYS
   - Ensure JWT token is not expired

2. **403 Forbidden / Path Access Denied**
   - Check filesystem boundaries configuration
   - Verify requested path is within allowed roots
   - Check user scopes for operation

3. **JWT Validation Errors**
   - Install python-jose: `pip install python-jose`
   - Verify JWT_SECRET matches token signing key
   - Check token issuer/audience claims

### Debug Mode

Enable detailed logging:
```bash
export PYTHONPATH=. 
export LOG_LEVEL=DEBUG
python kyros-mcp/main.py
```

## Security Compliance

This implementation meets the following standards:

- **MCP June 2025 Specification**: Full OAuth Resource Server compliance
- **OAuth 2.1**: Bearer token authentication with PKCE support
- **RFC 8707**: Resource indicators for token audience restriction
- **OWASP Guidelines**: Protection against common web vulnerabilities
- **Zero Trust**: All requests authenticated and authorized

## Support

For security issues or questions:
- Review this documentation
- Run the test suite: `python test_mcp_security.py`
- Check security audit logs
- Verify environment configuration

**Security Disclosure**: Report security vulnerabilities through secure channels only.