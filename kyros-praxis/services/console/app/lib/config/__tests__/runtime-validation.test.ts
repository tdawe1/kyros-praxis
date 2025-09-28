/**
 * @jest-environment node
 */

import { performRuntimeValidation, validateOnStartup } from '../runtime-validation';

// Mock fetch for external service tests
global.fetch = jest.fn();

const originalEnv = process.env;

beforeEach(() => {
  jest.resetModules();
  jest.clearAllMocks();
  process.env = { ...originalEnv };
});

afterAll(() => {
  process.env = originalEnv;
});

describe('Runtime Validation', () => {
  describe('performRuntimeValidation', () => {
    test('should perform comprehensive validation with valid config', async () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'development',
        NEXTAUTH_SECRET: 'a'.repeat(64),
        NEXT_PUBLIC_APP_URL: 'http://localhost:3000',
        NEXT_PUBLIC_API_URL: 'http://localhost:8000/api/v1',
      };

      // Mock successful API health check
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
      });

      const summary = await performRuntimeValidation();

      expect(summary.overall).toBe('healthy');
      expect(summary.totalChecks).toBeGreaterThan(0);
      expect(summary.passed).toBeGreaterThan(0);
      expect(summary.duration).toBeGreaterThan(0);
    });

    test('should detect environment validation failures', async () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'development',
        NEXTAUTH_SECRET: 'short', // Invalid secret
      };

      const summary = await performRuntimeValidation();

      expect(summary.overall).toBe('critical');
      expect(summary.critical).toBeGreaterThan(0);
      
      const envFailure = summary.results.find(
        r => r.component === 'environment' && !r.success
      );
      expect(envFailure).toBeDefined();
    });

    test('should detect weak secret strength', async () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'development',
        NEXTAUTH_SECRET: 'weakSecretThatIsLongEnoughButStillWeak123', // Long but weak
        NEXT_PUBLIC_APP_URL: 'http://localhost:3000',
        NEXT_PUBLIC_API_URL: 'http://localhost:8000/api/v1',
      };

      const summary = await performRuntimeValidation();

      // Should have warnings about secret strength
      const secretCheck = summary.results.find(
        r => r.checkName === 'nextauth_secret_strength'
      );
      expect(secretCheck).toBeDefined();
    });
  });

  describe('production security checks', () => {
    test('should detect dev login enabled in production', async () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'production',
        NEXTAUTH_SECRET: 'a'.repeat(64),
        NEXT_PUBLIC_APP_URL: 'https://kyros-praxis.com',
        NEXT_PUBLIC_ALLOW_DEV_LOGIN: 'true', // Security issue
      };

      const summary = await performRuntimeValidation();

      expect(summary.overall).toBe('critical');
      
      const devBypassCheck = summary.results.find(
        r => r.checkName === 'dev_bypass_disabled' && !r.success
      );
      expect(devBypassCheck).toBeDefined();
      expect(devBypassCheck?.severity).toBe('critical');
    });

    test('should validate HTTPS URLs in production', async () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'production',
        NEXTAUTH_SECRET: 'a'.repeat(64),
        NEXT_PUBLIC_APP_URL: 'http://kyros-praxis.com', // Should be HTTPS
        SENTRY_DSN: 'https://example@sentry.io/project',
      };

      const summary = await performRuntimeValidation();

      expect(summary.overall).toBe('critical');
      
      // Should fail environment validation for HTTP URL
      const envFailure = summary.results.find(
        r => r.component === 'environment' && !r.success
      );
      expect(envFailure).toBeDefined();
    });

    test('should warn about missing Sentry in production', async () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'production',
        NEXTAUTH_SECRET: 'a'.repeat(64),
        NEXT_PUBLIC_APP_URL: 'https://kyros-praxis.com',
        NEXT_PUBLIC_API_URL: 'https://api.kyros-praxis.com/api/v1',
        NEXT_PUBLIC_ALLOW_DEV_LOGIN: 'false',
        ALLOW_DEV_LOGIN: '0',
        // SENTRY_DSN missing
      };

      const summary = await performRuntimeValidation();

      const sentryWarning = summary.results.find(
        r => r.checkName === 'sentry_monitoring' && r.severity === 'warning'
      );
      expect(sentryWarning).toBeDefined();
    });
  });

  describe('external service connectivity', () => {
    test('should validate successful API connectivity', async () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'development',
        NEXTAUTH_SECRET: 'a'.repeat(32),
        NEXT_PUBLIC_API_URL: 'http://localhost:8000/api/v1',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
      });

      const summary = await performRuntimeValidation();

      const apiCheck = summary.results.find(
        r => r.checkName === 'api_health_check' && r.success
      );
      expect(apiCheck).toBeDefined();
      expect(apiCheck?.severity).toBe('info');
    });

    test('should detect API connectivity failures', async () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'development',
        NEXTAUTH_SECRET: 'a'.repeat(32),
        NEXT_PUBLIC_API_URL: 'http://localhost:8000/api/v1',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      const summary = await performRuntimeValidation();

      const apiCheck = summary.results.find(
        r => r.checkName === 'api_health_check' && !r.success
      );
      expect(apiCheck).toBeDefined();
      expect(apiCheck?.severity).toBe('error');
    });

    test('should handle API timeout gracefully', async () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'development',
        NEXTAUTH_SECRET: 'a'.repeat(32),
        NEXT_PUBLIC_API_URL: 'http://localhost:8000/api/v1',
      };

      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('timeout'));

      const summary = await performRuntimeValidation();

      const apiCheck = summary.results.find(
        r => r.checkName === 'api_health_check' && !r.success
      );
      expect(apiCheck).toBeDefined();
    });
  });

  describe('validateOnStartup', () => {
    test('should pass with valid configuration', async () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'development',
        NEXTAUTH_SECRET: 'a'.repeat(32),
        NEXT_PUBLIC_APP_URL: 'http://localhost:3000',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
      });

      const summary = await validateOnStartup(false);
      expect(summary).toBeDefined();
    });

    test('should throw on critical issues when configured', async () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'production',
        NEXTAUTH_SECRET: 'short', // Critical issue
      };

      await expect(validateOnStartup(true)).rejects.toThrow();
    });

    test('should not throw on critical issues when disabled', async () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'production',
        NEXTAUTH_SECRET: 'short', // Critical issue
      };

      const summary = await validateOnStartup(false);
      expect(summary.critical).toBeGreaterThan(0);
    });
  });

  describe('NextAuth URL validation', () => {
    test('should validate secure NextAuth URL in production', async () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'production',
        NEXTAUTH_URL: 'https://kyros-praxis.com',
        NEXTAUTH_SECRET: 'a'.repeat(64),
        NEXT_PUBLIC_APP_URL: 'https://kyros-praxis.com',
        NEXT_PUBLIC_API_URL: 'https://api.kyros-praxis.com/api/v1',
        SENTRY_DSN: 'https://example@sentry.io/project',
        NEXT_PUBLIC_ALLOW_DEV_LOGIN: 'false',
        ALLOW_DEV_LOGIN: '0',
      };

      const summary = await performRuntimeValidation();

      const nextAuthCheck = summary.results.find(
        r => r.checkName === 'nextauth_url_valid' && r.success
      );
      expect(nextAuthCheck).toBeDefined();
    });

    test('should reject HTTP NextAuth URL in production', async () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'production',
        NEXTAUTH_URL: 'http://kyros-praxis.com', // HTTP not allowed
        NEXTAUTH_SECRET: 'a'.repeat(64),
      };

      const summary = await performRuntimeValidation();

      const nextAuthCheck = summary.results.find(
        r => r.checkName === 'nextauth_url_secure' && !r.success
      );
      expect(nextAuthCheck).toBeDefined();
      expect(nextAuthCheck?.severity).toBe('error');
    });
  });
});