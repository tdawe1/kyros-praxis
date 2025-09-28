/**
 * @jest-environment node
 */

import { validateEnvironment, getValidatedEnvironment, isSecureForProduction } from '../env-validation';

// Mock process.env
const originalEnv = process.env;

beforeEach(() => {
  jest.resetModules();
  process.env = { ...originalEnv };
});

afterAll(() => {
  process.env = originalEnv;
});

describe('Environment Validation', () => {
  describe('validateEnvironment', () => {
    test('should validate development environment successfully', () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'development',
        NEXTAUTH_SECRET: 'a'.repeat(32), // 32 character secret
        NEXT_PUBLIC_APP_URL: 'http://localhost:3000',
        NEXT_PUBLIC_API_URL: 'http://localhost:8000/api/v1',
      };

      const result = validateEnvironment();
      
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data?.NODE_ENV).toBe('development');
    });

    test('should validate production environment with HTTPS URLs', () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'production',
        NEXTAUTH_SECRET: 'a'.repeat(64), // Strong secret
        NEXT_PUBLIC_APP_URL: 'https://kyros-praxis.com',
        NEXT_PUBLIC_API_URL: 'https://api.kyros-praxis.com/api/v1',
        SENTRY_DSN: 'https://example@sentry.io/project',
        NEXT_PUBLIC_ALLOW_DEV_LOGIN: 'false',
        ALLOW_DEV_LOGIN: '0',
      };

      const result = validateEnvironment();
      
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
    });

    test('should fail validation for short NEXTAUTH_SECRET', () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'development',
        NEXTAUTH_SECRET: 'short', // Too short
      };

      const result = validateEnvironment();
      
      expect(result.success).toBe(false);
      expect(result.errors).toBeDefined();
      expect(result.errors?.some(e => e.field === 'NEXTAUTH_SECRET')).toBe(true);
    });

    test('should fail production validation with HTTP URLs', () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'production',
        NEXTAUTH_SECRET: 'a'.repeat(32),
        NEXT_PUBLIC_APP_URL: 'http://kyros-praxis.com', // HTTP not allowed in production
        NEXT_PUBLIC_API_URL: 'http://api.kyros-praxis.com/api/v1',
      };

      const result = validateEnvironment();
      
      expect(result.success).toBe(false);
      expect(result.errors?.some(e => e.message.includes('HTTPS'))).toBe(true);
    });

    test('should fail production validation with dev login enabled', () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'production',
        NEXTAUTH_SECRET: 'a'.repeat(32),
        NEXT_PUBLIC_APP_URL: 'https://kyros-praxis.com',
        NEXT_PUBLIC_API_URL: 'https://api.kyros-praxis.com/api/v1',
        NEXT_PUBLIC_ALLOW_DEV_LOGIN: 'true', // Not allowed in production
        SENTRY_DSN: 'https://example@sentry.io/project',
      };

      const result = validateEnvironment();
      
      expect(result.success).toBe(false);
    });
  });

  describe('getValidatedEnvironment', () => {
    test('should return validated environment for valid config', () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'development',
        NEXTAUTH_SECRET: 'a'.repeat(32),
        NEXT_PUBLIC_APP_URL: 'http://localhost:3000',
        NEXT_PUBLIC_API_URL: 'http://localhost:8000/api/v1',
      };

      const env = getValidatedEnvironment();
      
      expect(env.NODE_ENV).toBe('development');
      expect(env.NEXTAUTH_SECRET).toBeDefined();
    });

    test('should throw error for invalid config', () => {
      process.env = {
        ...originalEnv,
        NEXTAUTH_SECRET: 'short', // Invalid
      };

      expect(() => getValidatedEnvironment()).toThrow();
    });
  });

  describe('isSecureForProduction', () => {
    test('should return secure true for valid production config', () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'production',
        NEXTAUTH_SECRET: 'a'.repeat(64),
        NEXT_PUBLIC_APP_URL: 'https://kyros-praxis.com',
        NEXT_PUBLIC_API_URL: 'https://api.kyros-praxis.com/api/v1',
        SENTRY_DSN: 'https://example@sentry.io/project',
        NEXT_PUBLIC_ALLOW_DEV_LOGIN: 'false',
        ALLOW_DEV_LOGIN: '0',
      };

      const result = isSecureForProduction();
      
      expect(result.secure).toBe(true);
      expect(result.issues).toHaveLength(0);
    });

    test('should return secure false for invalid production config', () => {
      process.env = {
        ...originalEnv,
        NODE_ENV: 'production',
        NEXTAUTH_SECRET: 'short',
        NEXT_PUBLIC_ALLOW_DEV_LOGIN: 'true',
      };

      const result = isSecureForProduction();
      
      expect(result.secure).toBe(false);
      expect(result.issues.length).toBeGreaterThan(0);
    });
  });

  describe('default values', () => {
    test('should apply correct defaults', () => {
      process.env = {
        ...originalEnv,
        NEXTAUTH_SECRET: 'a'.repeat(64), // Use strong secret to avoid warnings
      };

      const result = validateEnvironment();
      
      expect(result.success).toBe(true);
      expect(result.data?.PORT).toBe(3000);
      expect(result.data?.NEXT_PUBLIC_ALLOW_DEV_LOGIN).toBe('false');
    });
  });
});