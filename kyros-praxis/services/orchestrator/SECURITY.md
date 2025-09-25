# Kyros Orchestrator Security Architecture

This document provides an overview of the security architecture for the Kyros Orchestrator service, explaining how the authentication and security modules work together to provide comprehensive protection.

## Overview

The Kyros Orchestrator implements a multi-layered security approach using several key components:

1. **Authentication Module** (`auth.py`) - Handles user authentication, password verification, and JWT token management
2. **Security Middleware** (`security_middleware.py`) - Provides CSRF protection, rate limiting, security headers, and HTTPS enforcement
3. **API Key Middleware** (`middleware.py`) - Offers additional API key-based authentication and rate limiting

These components work together to create a defense-in-depth security model that protects against common web application vulnerabilities.

## Authentication Flow

The authentication system follows this flow:

1. **User Login**: Users provide credentials to the `/auth/login` endpoint
2. **Password Verification**: The system verifies the password using bcrypt hashing
3. **Token Creation**: A JWT token is created with appropriate claims and expiration
4. **Token Validation**: Subsequent requests include the JWT in the Authorization header
5. **User Resolution**: The system decodes the JWT and retrieves the user from the database

### JWT Token Management

The system implements JWT best practices:

- **Secure Signing**: Uses HS512 algorithm with cryptographically secure secret keys
- **Standard Claims**: Includes expiration (exp), issuer (iss), audience (aud), and issued at (iat) claims
- **Appropriate Expiration**: Tokens expire after a configurable period (default: 2 hours)
- **Validation**: Tokens are validated on every authenticated request

### Password Security

Password handling follows security best practices:

- **Hashing Algorithm**: Uses bcrypt for secure password hashing
- **Salt**: Automatically generates and manages unique salts for each password
- **Constant-time Comparison**: Prevents timing attacks during password verification

## Security Middleware Protection

The security middleware provides multiple layers of protection:

### CSRF Protection

Cross-Site Request Forgery protection is implemented for web form submissions:

- **Token Generation**: Cryptographically signed tokens with timestamps
- **Session Binding**: Optional binding of tokens to user sessions
- **Dual Transmission**: Tokens can be sent via headers or cookies
- **Validation**: Secure validation with constant-time comparison

### Rate Limiting

Rate limiting prevents abuse and ensures fair usage:

- **Distributed Storage**: Uses Redis for multi-instance deployments
- **In-memory Fallback**: Falls back to in-memory storage when Redis is unavailable
- **Client Identification**: Tracks requests by user ID or IP address
- **Configurable Limits**: Adjustable request limits and time windows

### Security Headers

The middleware automatically adds security headers to all responses:

- **Content Security Policy (CSP)**: Controls allowed content sources
- **HTTP Strict Transport Security (HSTS)**: Enforces HTTPS in production
- **X-Content-Type-Options**: Prevents MIME type sniffing
- **X-Frame-Options**: Prevents clickjacking attacks
- **X-XSS-Protection**: Enables browser XSS protection

### HTTPS Enforcement

In production environments, the middleware enforces HTTPS:

- **Protocol Checking**: Validates HTTPS protocol on incoming requests
- **Forwarded Headers**: Properly handles reverse proxy configurations
- **Automatic Rejection**: Rejects HTTP requests in production

## Integration Points

### FastAPI Dependency Injection

The authentication system integrates with FastAPI's dependency injection:

```python
@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello, {current_user.username}!"}
```

### Middleware Chain

Security measures are applied in this order:

1. HTTPS enforcement (if configured)
2. Rate limiting
3. CSRF protection for state-changing methods
4. Security headers added to responses
5. CSRF token generation for GET requests

### Configuration Management

Security settings are centralized and configurable:

- **Environment-based Configuration**: Different settings for development and production
- **External Secret Management**: Integration with secret management systems
- **Runtime Adjustments**: Some settings can be adjusted without code changes

## Security Best Practices Implementation

### Defense in Depth

The system implements multiple overlapping security controls:

- **Authentication**: Verifies user identity
- **Authorization**: Controls access to resources
- **Input Validation**: Validates all incoming data
- **Output Encoding**: Prevents injection attacks
- **Error Handling**: Prevents information leakage

### Secure Defaults

The system is configured with secure defaults:

- **CSRF Protection Enabled**: By default for web forms
- **HTTPS Enforced**: In production environments
- **Secure Cookies**: Marked as secure and HTTP-only
- **Restrictive CORS**: Limited to known origins

### Monitoring and Logging

Security events are logged for monitoring:

- **Authentication Attempts**: Both successful and failed attempts
- **Rate Limiting**: When clients are rate limited
- **CSRF Violations**: Invalid token submissions
- **Security Violations**: CSP violations and other security events

## Usage Examples

### Protecting an Endpoint

```python
from fastapi import Depends
from auth import get_current_user, User

@app.get("/user/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "email": current_user.email}
```

### Creating a Token

```python
from auth import authenticate_user, create_access_token
from database import get_db

def login(username: str, password: str, db = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
```

## Future Enhancements

Planned security improvements include:

- **Token Revocation**: JWT token blacklist for immediate revocation
- **Multi-factor Authentication**: Support for additional authentication factors
- **Session Management**: Server-side session tracking
- **Audit Logging**: Comprehensive security event logging
- **Advanced Rate Limiting**: Adaptive rate limiting based on behavior