import { z } from 'zod';

/**
 * Environment Variable Validation Schema
 * 
 * This module provides comprehensive validation for all environment variables
 * used by the Console service, ensuring secure defaults and proper validation
 * of sensitive configuration data.
 */

// Security-focused validation helpers
const secretMinLength = 32;
const isValidUrl = (url: string) => {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
};

// Base environment schema
const BaseEnvironmentSchema = z.object({
  // Node.js environment
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  
  // Port configuration
  PORT: z.coerce.number().int().min(1).max(65535).default(3000),
  
  // Next.js configuration
  NEXT_PUBLIC_APP_URL: z.string().url().default('https://kyros-praxis.com'),
  NEXT_PUBLIC_API_URL: z.string().url().default('http://localhost:8000/api/v1'),
  NEXT_PUBLIC_AUTH_URL: z.string().url().optional(),
  
  // NextAuth configuration - security critical
  NEXTAUTH_SECRET: z.string()
    .min(secretMinLength, `NEXTAUTH_SECRET must be at least ${secretMinLength} characters`)
    .regex(/^[A-Za-z0-9+/=]+$/, 'NEXTAUTH_SECRET must be a valid base64-encoded string'),
  NEXTAUTH_URL: z.string().url().optional(),
  
  // Development bypass (should be disabled in production)
  NEXT_PUBLIC_ALLOW_DEV_LOGIN: z.enum(['true', 'false']).default('false'),
  ALLOW_DEV_LOGIN: z.enum(['0', '1']).default('0'),
  
  // Sentry configuration
  SENTRY_DSN: z.string().url().optional(),
  SENTRY_ORG: z.string().optional(),
  SENTRY_PROJECT: z.string().optional(),
  SENTRY_AUTH_TOKEN: z.string().optional(),
  
  // CI/Build environment
  CI: z.enum(['true', 'false']).optional(),
  VERCEL: z.enum(['1']).optional(),
  VERCEL_ENV: z.enum(['development', 'preview', 'production']).optional(),
});

// Production-specific validation rules
const ProductionEnvironmentSchema = BaseEnvironmentSchema.extend({
  // In production, dev login must be disabled
  NEXT_PUBLIC_ALLOW_DEV_LOGIN: z.literal('false'),
  ALLOW_DEV_LOGIN: z.literal('0'),
  
  // Production URLs must use HTTPS
  NEXT_PUBLIC_APP_URL: z.string().refine(
    (url) => url.startsWith('https://'),
    'NEXT_PUBLIC_APP_URL must use HTTPS in production'
  ),
  NEXT_PUBLIC_API_URL: z.string().refine(
    (url) => url.startsWith('https://'),
    'NEXT_PUBLIC_API_URL must use HTTPS in production'
  ),
  
  // Sentry should be configured in production
  SENTRY_DSN: z.string().url(),
});

// Development-specific validation (more permissive)
const DevelopmentEnvironmentSchema = BaseEnvironmentSchema.extend({
  // Allow HTTP in development
  NEXT_PUBLIC_API_URL: z.string().refine(isValidUrl, 'Must be a valid URL'),
  NEXT_PUBLIC_APP_URL: z.string().refine(isValidUrl, 'Must be a valid URL'),
});

/**
 * Validates environment variables based on the current NODE_ENV
 */
export function validateEnvironment() {
  const env = process.env;
  const nodeEnv = env.NODE_ENV || 'development';
  
  // Choose schema based on environment
  const schema = nodeEnv === 'production' 
    ? ProductionEnvironmentSchema 
    : DevelopmentEnvironmentSchema;
  
  try {
    const validated = schema.parse(env);
    
    // Additional security checks
    performSecurityChecks(validated, nodeEnv);
    
    return {
      success: true,
      data: validated,
      warnings: generateWarnings(validated, nodeEnv),
    };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        success: false,
        errors: error.errors.map(err => ({
          field: err.path.join('.'),
          message: err.message,
          code: err.code,
        })),
      };
    }
    
    return {
      success: false,
      errors: [{ field: 'unknown', message: 'Unexpected validation error', code: 'unknown' }],
    };
  }
}

/**
 * Performs additional security checks beyond basic validation
 */
function performSecurityChecks(config: any, nodeEnv: string) {
  const checks: Array<{ name: string; passed: boolean; message: string }> = [];
  
  // Check for default/weak secrets
  const defaultSecrets = [
    'changethis',
    'your_secret_key_here',
    'your-secret-key-here',
    'secret',
    'password',
    'default',
  ];
  
  if (defaultSecrets.some(secret => config.NEXTAUTH_SECRET?.toLowerCase().includes(secret))) {
    checks.push({
      name: 'nextauth_secret_strength',
      passed: false,
      message: 'NEXTAUTH_SECRET appears to use a default or weak value',
    });
  }
  
  // Check secret entropy (basic check)
  if (config.NEXTAUTH_SECRET && config.NEXTAUTH_SECRET.length < 64) {
    checks.push({
      name: 'nextauth_secret_length',
      passed: false,
      message: 'NEXTAUTH_SECRET should be at least 64 characters for optimal security',
    });
  }
  
  // Production security requirements
  if (nodeEnv === 'production') {
    if (!config.SENTRY_DSN) {
      checks.push({
        name: 'sentry_monitoring',
        passed: false,
        message: 'Sentry monitoring should be configured in production',
      });
    }
  }
  
  // Log failed security checks
  const failedChecks = checks.filter(check => !check.passed);
  if (failedChecks.length > 0) {
    console.warn('🔒 Security Configuration Warnings:');
    failedChecks.forEach(check => {
      console.warn(`  ⚠️  ${check.name}: ${check.message}`);
    });
  }
}

/**
 * Generates configuration warnings for potential issues
 */
function generateWarnings(config: any, nodeEnv: string): string[] {
  const warnings: string[] = [];
  
  if (nodeEnv === 'development' && config.NEXT_PUBLIC_ALLOW_DEV_LOGIN === 'true') {
    warnings.push('Development login bypass is enabled - ensure this is disabled in production');
  }
  
  if (!config.NEXTAUTH_URL && nodeEnv === 'production') {
    warnings.push('NEXTAUTH_URL should be explicitly set in production');
  }
  
  return warnings;
}

/**
 * Type-safe access to validated environment configuration
 */
export type ValidatedEnvironment = z.infer<typeof BaseEnvironmentSchema>;

/**
 * Gets the validated environment configuration
 * Throws an error if validation fails
 */
export function getValidatedEnvironment(): ValidatedEnvironment {
  const result = validateEnvironment();
  
  if (!result.success) {
    const errorMessages = result.errors?.map(err => `${err.field}: ${err.message}`).join('\n') || 'Unknown validation error';
    throw new Error(`Environment validation failed:\n${errorMessages}`);
  }
  
  if (result.warnings && result.warnings.length > 0) {
    console.warn('🔧 Configuration Warnings:');
    result.warnings.forEach(warning => console.warn(`  ⚠️  ${warning}`));
  }
  
  return result.data!;
}

/**
 * Checks if the current environment is secure for production use
 */
export function isSecureForProduction(): { secure: boolean; issues: string[] } {
  const result = validateEnvironment();
  const issues: string[] = [];
  
  if (!result.success) {
    issues.push(...(result.errors?.map(err => err.message) || []));
  }
  
  if (result.warnings) {
    issues.push(...result.warnings);
  }
  
  // Additional production readiness checks
  if (process.env.NODE_ENV === 'production') {
    if (process.env.NEXT_PUBLIC_ALLOW_DEV_LOGIN === 'true') {
      issues.push('Development login bypass must be disabled in production');
    }
    
    if (!process.env.SENTRY_DSN) {
      issues.push('Sentry monitoring should be configured for production error tracking');
    }
  }
  
  return {
    secure: issues.length === 0,
    issues,
  };
}