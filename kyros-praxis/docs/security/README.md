# Security Guidelines

This document outlines security best practices and requirements for developing and deploying Kyros Praxis.

## 🔐 Security Principles

### Core Security Tenets
1. **Defense in Depth** - Multiple layers of security controls
2. **Least Privilege** - Services and users have minimum required access
3. **Zero Trust** - Never trust, always verify
4. **Secure by Default** - Security features enabled by default

## 🛡️ Authentication & Authorization

### Authentication Requirements
- **JWT Tokens**: Must use RS256 or HS256 with strong secrets
- **Token Expiration**: Maximum 24 hours for access tokens
- **Refresh Tokens**: Separate refresh tokens with longer expiration
- **Multi-factor**: Consider MFA for production deployments

### Authorization Requirements
- **Role-based Access Control (RBAC)**: ✅ **IMPLEMENTED** - Granular permissions system with user/moderator/admin roles
- **Service-to-Service Auth**: Use mutual TLS or API keys for internal communication
- **Session Management**: Implement secure session handling with timeout

#### RBAC Implementation Details

**User Roles:**
- **User**: Basic access (jobs:read, jobs:create, tasks:read, tasks:create)
- **Moderator**: Extended permissions (job updates, user read access, log access)
- **Admin**: Full system access (all permissions including user management)

**Permission System:**
```python
# Route protection with specific permissions
@router.post("/jobs")
async def create_job(
    current_user: User = Depends(require_permission(Permission.CREATE_JOBS))
):
    pass

# Role-based protection
@router.get("/admin/users")
async def list_users(
    current_user: User = Depends(require_role(Role.ADMIN))
):
    pass
```

**Available Permissions:**
- Job Management: `jobs:read`, `jobs:create`, `jobs:update`, `jobs:delete`
- Task Management: `tasks:read`, `tasks:create`, `tasks:update`, `tasks:delete`
- User Management: `users:read`, `users:create`, `users:update`, `users:delete`
- System Administration: `system:admin`, `logs:read`, `settings:manage`

## 🔒 Secret Management

### Environment Variables
```bash
# Required secrets (minimum 32 characters each)
JWT_SECRET=your_very_secure_jwt_secret_minimum_32_chars
NEXTAUTH_SECRET=your_very_secure_nextauth_secret_minimum_32_chars
SECRET_KEY=your_very_secure_app_secret_minimum_32_chars
CSRF_SECRET=your_very_secure_csrf_secret_minimum_32_chars
DATABASE_PASSWORD=your_very_secure_db_password_minimum_32_chars
```

### Secret Generation
```bash
# Generate secure secrets
openssl rand -hex 32  # 64-character hex string
openssl rand -base64 32  # Base64 encoded
```

### Secret Rotation
- **Rotation Frequency**: Every 90 days for production
- **Grace Period**: 7-day overlap during rotation
- **Automated Rotation**: Implement automated secret rotation in production

## 🌐 Web Security

### Content Security Policy (CSP)
```http
Content-Security-Policy: default-src 'self'; 
script-src 'self' 'nonce-<random-value>'; 
style-src 'self' 'nonce-<random-value>'; 
img-src 'self' data: https:; 
font-src 'self' data:;
connect-src 'self' wss:;
frame-ancestors 'none';
form-action 'self';
base-uri 'self';
```

### Security Headers
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### CSRF Protection
- **HMAC-based tokens** with timestamp validation
- **Token expiration**: 1 hour maximum
- **Secure storage**: HttpOnly, Secure, SameSite=Strict cookies

## 🗄️ Database Security

### Connection Security
- **TLS/SSL encryption** for all database connections
- **Connection pooling** with secure configuration
- **Parameterized queries** to prevent SQL injection
- **Least privilege** database users

### Data Protection
- **Encryption at rest**: Enable PostgreSQL TDE or filesystem encryption
- **Encryption in transit**: Always use TLS
- **Data masking**: Mask sensitive data in logs and responses
- **Backup encryption**: Encrypt all database backups

### Query Security
```python
# Always use parameterized queries
# BAD: String concatenation
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# GOOD: Parameterized query
query = "SELECT * FROM users WHERE name = :username"
params = {"username": user_input}
```

## 🔐 API Security

### Input Validation
- **Validate all inputs** against strict schemas
- **Sanitize user-generated content**
- **Implement rate limiting** per endpoint
- **Use API gateways** for traffic management

### Output Encoding
- **Escape all output** to prevent XSS
- **Use template engine auto-escaping**
- **Implement content type validation**
- **Sanitize file uploads**

### Rate Limiting
```python
# Rate limiting configuration
RATE_LIMIT_REQUESTS = 100  # requests per window
RATE_LIMIT_WINDOW = 900    # 15 minutes in seconds
RATE_LIMIT_BURST = 10      # burst capacity
```

## 🔄 Infrastructure Security

### Container Security
- **Non-root containers**: Run containers as non-root users
- **Read-only filesystems**: Where possible
- **Resource limits**: Set CPU and memory limits
- **Health checks**: Implement comprehensive health checks

### Network Security
- **Network segmentation**: Separate services by security level
- **Firewall rules**: Restrict traffic between services
- **VPN/Private Networks**: Use for internal communication
- **DDoS protection**: Implement at network edge

### Monitoring & Logging
- **Structured logging**: JSON format with consistent fields
- **Security events**: Log authentication attempts, access violations
- **Log retention**: 90 days minimum, 1 year for security logs
- **Real-time monitoring**: Alert on security events

## 🚨 Incident Response

### Security Incident Process
1. **Detection**: Automated monitoring and alerts
2. **Assessment**: Determine scope and impact
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove threat and patch vulnerabilities
5. **Recovery**: Restore services with security controls
6. **Lessons Learned**: Update security measures

### Incident Response Team
- **Incident Commander**: Overall coordination
- **Security Lead**: Technical investigation
- **Communications**: Stakeholder notification
- **Operations**: Service restoration

## 🧪 Security Testing

### Automated Testing
- **SAST/DAST tools**: Static and dynamic analysis
- **Dependency scanning**: Check for known vulnerabilities
- **Secret detection**: Scan code for hardcoded secrets
- **Configuration validation**: Ensure secure configurations

### Manual Testing
- **Penetration testing**: Annual third-party assessment
- **Code reviews**: Security-focused code reviews
- **Architecture reviews**: Security design validation
- **Threat modeling**: Identify potential attack vectors

## 📋 Security Checklist

### Development Checklist
- [ ] No hardcoded secrets in code
- [ ] All inputs are validated
- [ ] SQL queries are parameterized
- [ ] XSS protection implemented
- [ ] CSRF protection enabled
- [ ] Authentication and authorization checks
- [ ] Error handling doesn't expose sensitive information
- [ ] Logging includes security events
- [ ] Dependencies are scanned for vulnerabilities

### Deployment Checklist
- [ ] All secrets are environment variables
- [ ] TLS certificates are valid
- [ ] Security headers are configured
- [ ] Database connections are encrypted
- [ ] Rate limiting is enabled
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery procedures tested
- [ ] Incident response team contact information updated

### Production Checklist
- [ ] Security monitoring active
- [ ] Log aggregation configured
- [ ] Intrusion detection systems active
- [ ] Backup encryption verified
- [ ] Disaster recovery tested
- [ ] Security policies documented
- [ ] Security training completed for all team members

## 🔗 Additional Resources

- [OWASP Security Guidelines](https://owasp.org/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Security Controls](https://www.cisecurity.org/controls/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

## 📞 Security Contacts

- **Security Team**: security@kyros-praxis.com
- **Emergency Security**: +1-555-SECURE
- **Vulnerability Reporting**: security@kyros-praxis.com

For security questions or to report vulnerabilities, please contact our security team.