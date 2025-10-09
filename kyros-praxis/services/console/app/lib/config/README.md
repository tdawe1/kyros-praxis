# Secure Configuration Management

This directory contains the comprehensive secure configuration management system for the Console service.

## Overview

The secure configuration system provides:
- Environment variable validation with strict schemas
- Secure secret management and encryption
- Runtime configuration validation
- Configuration change auditing
- Production readiness checks

## Components

### `env-validation.ts`
Environment variable validation using Zod schemas:
- Validates all environment variables on startup
- Different validation rules for development vs production
- Security strength checking for secrets
- Automatic detection of insecure configurations

### `secrets.ts`
Secure secret management:
- Cryptographically secure secret generation
- Secret strength validation with entropy analysis
- Encrypted storage for sensitive configuration
- Secret rotation scheduling and tracking

### `runtime-validation.ts`
Runtime configuration validation:
- Comprehensive startup validation checks
- External service connectivity testing
- Production readiness validation
- Configuration health monitoring

### `audit-logging.ts`
Configuration audit logging:
- Complete audit trail for configuration changes
- Security event logging with severity classification
- Secret access tracking
- Integration with existing logging systems

### `startup.ts`
Application startup integration:
- Initialization of secure configuration on startup
- Middleware for API route configuration checking
- Graceful handling of configuration failures

## Usage

### Initialization

```typescript
import { initializeSecureConfiguration } from './lib/config';

// Initialize during application startup
await initializeSecureConfiguration({
  throwOnCritical: process.env.NODE_ENV === 'production',
  enableAuditLogging: true,
});
```

### Environment Validation

```typescript
import { getValidatedEnvironment, validateEnvironment } from './lib/config';

// Get validated configuration
const config = getValidatedEnvironment();

// Or check validation result
const result = validateEnvironment();
if (!result.success) {
  console.error('Configuration errors:', result.errors);
}
```

### Secret Management

```typescript
import { 
  generateSecureSecret, 
  validateSecretStrength,
  secretStore 
} from './lib/config';

// Generate a secure secret
const secret = generateSecureSecret(64);

// Validate secret strength
const validation = validateSecretStrength(secret);
if (!validation.valid) {
  console.warn('Weak secret:', validation.issues);
}

// Store encrypted secret
secretStore.store('my-secret', secret, {
  name: 'My Secret',
  type: 'api_key',
  expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days
});
```

### Runtime Validation

```typescript
import { performRuntimeValidation, validateOnStartup } from './lib/config';

// Perform comprehensive validation
const summary = await performRuntimeValidation();
console.log(`Validation: ${summary.overall} (${summary.passed}/${summary.totalChecks} passed)`);

// Validate on startup (throws on critical issues)
await validateOnStartup(true);
```

### Health Monitoring

```typescript
import { getConfigurationHealth } from './lib/config';

const health = getConfigurationHealth();
if (health.status !== 'healthy') {
  console.warn('Configuration issues:', health.issues);
}
```

## Environment Variables

### Required Variables

- `NEXTAUTH_SECRET`: JWT signing secret (minimum 32 characters, recommended 64+)
- `NODE_ENV`: Environment (development/production/test)

### Optional Variables

- `PORT`: Application port (default: 3000)
- `NEXT_PUBLIC_APP_URL`: Public application URL
- `NEXT_PUBLIC_API_URL`: API base URL
- `SENTRY_DSN`: Sentry error tracking DSN
- `CONFIG_ENCRYPTION_SALT`: Salt for configuration encryption

### Development Variables (Must be disabled in production)

- `NEXT_PUBLIC_ALLOW_DEV_LOGIN`: Enable development login bypass
- `ALLOW_DEV_LOGIN`: Enable development login bypass (alternative)

## Security Features

### Environment Validation
- Strict schema validation for all environment variables
- Different validation rules for development vs production
- HTTPS enforcement in production environments
- Detection of insecure development features in production

### Secret Management
- Cryptographically secure secret generation using Node.js crypto
- Secret strength validation with entropy analysis
- AES-256-GCM encryption for sensitive configuration data
- Secret rotation scheduling and expiration tracking

### Audit Logging
- Complete audit trail for all configuration changes
- Security event logging with severity classification
- Integration with existing audit systems
- Tamper-evident logging with payload hashing

### Production Readiness
- Comprehensive production readiness checks
- External service connectivity validation
- Security configuration verification
- Monitoring and alerting integration

## API Endpoints

### GET `/api/health/config`
Returns configuration health status without exposing sensitive data.

### POST `/api/health/config`
Triggers configuration revalidation and returns updated health status.

## Testing

Comprehensive test suite covers all configuration components:

```bash
# Run configuration tests
npm test -- app/lib/config/__tests__

# Run specific test file
npm test -- app/lib/config/__tests__/env-validation.test.ts
```

## Best Practices

### Environment Configuration
1. Never commit real secrets to version control
2. Use strong, randomly generated secrets (minimum 32 characters)
3. Rotate secrets regularly in production
4. Disable development features in production
5. Use HTTPS URLs in production environments

### Secret Management
1. Generate secrets using cryptographically secure methods
2. Validate secret strength before use
3. Encrypt sensitive configuration at rest
4. Implement secret rotation schedules
5. Monitor secret access and usage

### Production Deployment
1. Run configuration validation before deployment
2. Ensure all critical issues are resolved
3. Monitor configuration health in production
4. Implement alerting for configuration failures
5. Maintain audit logs for compliance

## Troubleshooting

### Common Issues

**Environment validation failed:**
- Check that all required environment variables are set
- Ensure NEXTAUTH_SECRET meets minimum length requirements
- Verify HTTPS URLs are used in production

**Configuration not initialized:**
- Ensure `initializeSecureConfiguration()` is called during startup
- Check for critical configuration issues preventing initialization

**Weak secret warnings:**
- Generate stronger secrets using `generateSecureSecret()`
- Use minimum 32 characters for cryptographic secrets
- Include mixed case, numbers, and special characters

### Debug Mode

Enable debug logging for detailed configuration information:

```bash
NODE_ENV=development DEBUG=config:* npm run dev
```

## Contributing

When adding new configuration options:
1. Update the Zod schemas in `env-validation.ts`
2. Add appropriate validation rules
3. Include security considerations
4. Add comprehensive tests
5. Update documentation