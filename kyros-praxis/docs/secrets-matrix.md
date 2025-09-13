# Secrets Management Matrix for kyros-praxis

This document outlines all secrets required for the CI/CD pipeline and production deployment.

## Secret Categories

### 1. Application Secrets
**Environment Variables**: `.env.example`

| Variable | Environment | Owner | Rotation Policy | Notes |
|----------|-------------|-------|------------------|-------|
| `DATABASE_URL` | All | Platform Team | Quarterly | Different per environment |
| `REDIS_URL` | All | Platform Team | Quarterly | Shared staging/prod |
| `QDRANT_API_KEY` | All | Platform Team | Quarterly | Different per environment |
| `JWT_SECRET` | All | Security Team | Quarterly | High entropy, 64+ chars |
| `NEXTAUTH_SECRET` | All | Security Team | Quarterly | High entropy, 64+ chars |
| `SECRET_KEY` | All | Security Team | Quarterly | High entropy, 64+ chars |

### 2. CI/CD Platform Secrets

#### CircleCI
| Variable | Environment | Owner | Rotation Policy | Notes |
|----------|-------------|-------|------------------|-------|
| `CIRCLECI_TOKEN` | CI/CD | Platform Team | Quarterly | Project-scoped token |
| `GITHUB_TOKEN` | CI/CD | Platform Team | Quarterly | For PR comments |
| `VERCEL_TOKEN` | CI/CD | Platform Team | Quarterly | Automation token |
| `RAILWAY_TOKEN` | CI/CD | Platform Team | Quarterly | CLI automation token |

#### Vercel
| Variable | Environment | Owner | Rotation Policy | Notes |
|----------|-------------|-------|------------------|-------|
| `VERCEL_ORG_ID` | All | Platform Team | Never | Organization identifier |
| `VERCEL_PROJECT_ID` | All | Platform Team | Never | Project identifier |
| `NEXT_PUBLIC_SENTRY_DSN` | Production | DevOps Team | Quarterly | Error tracking |
| `NEXT_PUBLIC_API_BASE_URL` | Production | Platform Team | On deploy | Production API URL |

#### Railway
| Variable | Environment | Owner | Rotation Policy | Notes |
|----------|-------------|-------|------------------|-------|
| `RAILWAY_PROJECT_ID` | All | Platform Team | Never | Project identifier |
| `RAILWAY_ENVIRONMENT_ID` | Production | Platform Team | Never | Production env ID |

### 3. External Service Secrets

#### Authentication Providers
| Variable | Environment | Owner | Rotation Policy | Notes |
|----------|-------------|-------|------------------|-------|
| `GOOGLE_CLIENT_ID` | Production | Security Team | As needed | OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Production | Security Team | Quarterly | OAuth client secret |
| `GITHUB_CLIENT_ID` | Production | Security Team | As needed | OAuth client ID |
| `GITHUB_CLIENT_SECRET` | Production | Security Team | Quarterly | OAuth client secret |

#### Monitoring & Observability
| Variable | Environment | Owner | Rotation Policy | Notes |
|----------|-------------|-------|------------------|-------|
| `SENTRY_DSN` | All | DevOps Team | Quarterly | Error tracking DSN |
| `SENTRY_ORG` | All | DevOps Team | Never | Sentry organization |
| `SENTRY_PROJECT` | All | DevOps Team | Never | Sentry project |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | All | DevOps Team | As needed | OpenTelemetry collector |

#### Analytics
| Variable | Environment | Owner | Rotation Policy | Notes |
|----------|-------------|-------|------------------|-------|
| `NEXT_PUBLIC_GA_ID` | Production | Product Team | Never | Google Analytics ID |
| `NEXT_PUBLIC_POSTHOG_KEY` | Production | Product Team | Never | PostHog project key |
| `LAUNCHDARKLY_SDK_KEY` | All | Product Team | Never | Feature flags |

### 4. Database Secrets

#### PostgreSQL
| Variable | Environment | Owner | Rotation Policy | Notes |
|----------|-------------|-------|------------------|-------|
| `POSTGRES_PASSWORD` | All | Platform Team | Quarterly | Database password |
| `POSTGRES_USER` | All | Platform Team | Never | Database username |

#### Redis
| Variable | Environment | Owner | Rotation Policy | Notes |
|----------|-------------|-------|------------------|-------|
| `REDIS_PASSWORD` | All | Platform Team | Quarterly | Redis password |

### 5. Infrastructure Secrets

#### AWS (if used)
| Variable | Environment | Owner | Rotation Policy | Notes |
|----------|-------------|-------|------------------|-------|
| `AWS_ACCESS_KEY_ID` | Production | Platform Team | Quarterly | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | Production | Platform Team | Quarterly | IAM secret key |

#### Email
| Variable | Environment | Owner | Rotation Policy | Notes |
|----------|-------------|-------|------------------|-------|
| `SMTP_USER` | Production | DevOps Team | Quarterly | SMTP username |
| `SMTP_PASSWORD` | Production | DevOps Team | Quarterly | SMTP password |

## Environment-Specific Configuration

### Development Environment
- Use local services (localhost)
- Secrets can be stored in `.env.local`
- No real external service credentials

### Preview Environments (per PR)
- Database: `kyros_pr_${PR_NUMBER}`
- Qdrant: Separate API key per environment
- Temporary credentials with short TTL
- Auto-destroyed on PR close

### Staging Environment
- Mirror production configuration
- Separate database instance
- Staging-specific external service credentials
- Regular credential rotation

### Production Environment
- High-security credentials
- Regular security audits
- Multi-factor authentication for access
- Detailed audit logging

## Secret Management Best Practices

### 1. Storage
- **Never commit secrets to Git**
- Use platform-specific secret managers
- Implement secret scanning in CI/CD

### 2. Access Control
- **Principle of least privilege**
- Role-based access control
- Regular access reviews
- Audit trails for secret access

### 3. Rotation
- **Automated rotation** where possible
- Quarterly manual rotation for critical secrets
- Immediate rotation on compromise detection
- Test rotation procedures regularly

### 4. Monitoring
- **Secret usage monitoring**
- Anomaly detection
- Automated alerts on suspicious activity
- Regular security audits

## Implementation Checklist

### CircleCI Secrets
- [ ] Configure project environment variables
- [ ] Set up context for production secrets
- [ ] Configure GitHub token for PR comments
- [ ] Add Vercel and Railway tokens

### Vercel Secrets
- [ ] Set up environment variables for production
- [ ] Configure preview environment variables
- [ ] Add Sentry DSN for error tracking
- [ ] Set up analytics keys

### Railway Secrets
- [ ] Configure production environment variables
- [ ] Set up database connection strings
- [ ] Add monitoring and observability keys
- [ ] Configure preview environment templates

### Local Development
- [ ] Create `.env.example` with all variables
- [ ] Document local setup procedures
- [ ] Provide mock data for development
- [ ] Set up local service configuration

## Security Considerations

1. **Secret Scanning**: Implement tools like GitGuardian or TruffleHog
2. **Audit Logging**: Track all secret access and modifications
3. **Backup and Recovery**: Secure backup procedures for critical secrets
4. **Disaster Recovery**: Procedures for secret compromise scenarios
5. **Compliance**: Ensure compliance with relevant security standards

## Rotation Procedures

### Automated Rotation
- Database passwords (via Railway)
- API keys (where supported)
- Temporary credentials

### Manual Rotation
- OAuth client secrets
- JWT secrets
- Third-party service credentials
- Infrastructure credentials

### Testing
- Regular rotation drills
- Verify application functionality post-rotation
- Test emergency rotation procedures