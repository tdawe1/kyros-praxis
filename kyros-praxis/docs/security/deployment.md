# Production Security Deployment Guide

This guide outlines the security configurations and procedures for deploying Kyros Praxis in production environments.

## 🔒 Pre-Deployment Security Checklist

### Environment Configuration
- [ ] Set `ENVIRONMENT=production` in environment variables
- [ ] Configure strong JWT secrets (minimum 32 characters, mixed case, numbers, symbols)
- [ ] Enable HTTPS/TLS with valid certificates
- [ ] Configure secure database connections with encryption
- [ ] Set up Redis for distributed rate limiting (production deployments)

### Authentication & Authorization
- [ ] Review user roles and permissions
- [ ] Verify RBAC implementation is working correctly
- [ ] Test authentication flows (login, token refresh, logout)
- [ ] Validate permission checks on all protected endpoints
- [ ] Enable audit logging for all authentication/authorization events

### Security Headers & Middleware
- [ ] Enable security middleware with production configuration
- [ ] Verify CSP (Content Security Policy) headers
- [ ] Enable HSTS (HTTP Strict Transport Security)
- [ ] Configure secure cookie settings
- [ ] Enable X-Frame-Options and X-Content-Type-Options headers

### Rate Limiting
- [ ] Configure production rate limits (default: 100 req/15min)
- [ ] Set up Redis backend for distributed rate limiting
- [ ] Test rate limiting with load testing tools
- [ ] Configure burst protection for API endpoints

## 🛡️ Security Configuration

### Environment Variables (Production)

```bash
# Core Security
ENVIRONMENT=production
SECRET_KEY=your_very_secure_secret_minimum_32_chars_with_special_chars
JWT_SECRET=your_jwt_secret_minimum_32_chars_with_special_chars
CSRF_SECRET=your_csrf_secret_minimum_32_chars_with_special_chars

# JWT Configuration  
JWT_ALGORITHM=RS256  # More secure for production
ACCESS_TOKEN_EXPIRE_MINUTES=30  # Shorter lifetime for production
JWT_ISSUER=kyros-praxis-prod
JWT_AUDIENCE=kyros-api

# Database Security
DATABASE_URL=postgresql://user:password@host:5432/db?sslmode=require
DATABASE_PASSWORD=secure_database_password

# Redis (for rate limiting)
REDIS_URL=redis://localhost:6379/0

# TLS/HTTPS
FORCE_HTTPS=true
HSTS_ENABLED=true
SECURE_COOKIES=true

# Rate Limiting (Production)
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=900
RATE_LIMIT_BURST=20

# Security Features
CSRF_ENABLED=true
CSP_ENABLED=true
AUDIT_ALL_REQUESTS=true
FAILED_AUTH_LOCKOUT_ENABLED=true
```

### Nginx Configuration (Example)

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/certificate.pem;
    ssl_certificate_key /path/to/private-key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Rate Limiting (additional layer)
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔍 Security Monitoring

### Audit Logging
- All authentication/authorization events are logged automatically
- Audit logs include: user ID, IP address, action, timestamp, result
- Logs are structured JSON format for easy analysis
- Failed authentication attempts trigger security alerts

### Security Metrics to Monitor
- Failed login attempts per minute/hour
- Permission denied events
- Rate limit violations
- Unusual access patterns
- Token expiration/validation failures

### Alerting Thresholds
- **High Priority**: 10+ failed logins from same IP in 5 minutes
- **Medium Priority**: 50+ rate limit violations in 15 minutes  
- **Low Priority**: Unusual access patterns or new user agents

## 🚨 Incident Response

### Security Incident Types
1. **Authentication Bypass**: Unauthorized access to protected resources
2. **Privilege Escalation**: User accessing resources above their permission level
3. **Brute Force Attack**: Repeated failed authentication attempts
4. **Rate Limit Abuse**: Excessive API requests violating rate limits

### Response Procedures
1. **Immediate Response** (< 5 minutes):
   - Identify affected users/resources
   - Block malicious IP addresses if necessary
   - Verify system integrity

2. **Investigation** (< 30 minutes):
   - Review audit logs for attack vectors
   - Identify scope of potential compromise
   - Document findings

3. **Containment** (< 1 hour):
   - Implement additional security measures
   - Reset compromised credentials if necessary
   - Update rate limiting rules

4. **Recovery** (< 4 hours):
   - Restore normal operations
   - Verify security measures are effective
   - Communicate with stakeholders

## 🔧 Security Testing

### Pre-Deployment Tests
```bash
# Run security tests
pytest services/orchestrator/tests/test_security.py -v
pytest services/orchestrator/tests/test_rbac.py -v

# Run authentication tests  
pytest services/orchestrator/tests/test_auth.py -v

# Security linting
ruff check services/orchestrator/ --select=S  # Security rules
```

### Load Testing with Security Focus
```bash
# Test rate limiting
for i in {1..200}; do
  curl -X GET "https://your-domain.com/api/v1/jobs" \
    -H "Authorization: Bearer $TOKEN" &
done
wait

# Test authentication performance
ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" \
  "https://your-domain.com/api/v1/jobs"
```

## 📋 Security Maintenance

### Regular Security Tasks (Weekly)
- [ ] Review audit logs for suspicious activity
- [ ] Check for security updates in dependencies
- [ ] Verify SSL certificate expiration dates
- [ ] Test backup and recovery procedures

### Security Tasks (Monthly)
- [ ] Review and update user permissions
- [ ] Rotate JWT signing secrets
- [ ] Update security documentation
- [ ] Conduct penetration testing
- [ ] Review rate limiting effectiveness

### Security Tasks (Quarterly)
- [ ] Full security audit
- [ ] Update security policies
- [ ] Security training for team
- [ ] Review incident response procedures

## 🏗️ Infrastructure Security

### Container Security
```dockerfile
# Use minimal base images
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set secure file permissions
COPY --chown=appuser:appuser . /app
USER appuser

# Use secrets management
RUN --mount=type=secret,id=jwt_secret \
    JWT_SECRET=$(cat /run/secrets/jwt_secret)
```

### Database Security
- Enable SSL/TLS for database connections
- Use connection pooling with authentication
- Regular security updates for database software
- Encrypted backups with secure key management

### Network Security
- Use VPC/private networks for internal communication
- Implement firewall rules (allow only necessary ports)
- Enable DDoS protection
- Monitor network traffic for anomalies