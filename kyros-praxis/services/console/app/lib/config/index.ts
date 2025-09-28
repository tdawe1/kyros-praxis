/**
 * Secure Configuration Management for Console Service
 * 
 * This module provides comprehensive secure configuration management including:
 * - Environment variable validation with Zod schemas
 * - Secure secret management and encryption
 * - Runtime configuration validation
 * - Configuration change auditing and logging
 * - Production readiness checks
 */

export * from './env-validation';
export * from './secrets';
export * from './runtime-validation';
export * from './audit-logging';

import { validateOnStartup, RuntimeValidationSummary } from './runtime-validation';
import { auditLogger } from './audit-logging';
import { getValidatedEnvironment } from './env-validation';

/**
 * Secure configuration interface
 */
export interface SecureConfiguration {
  environment: ReturnType<typeof getValidatedEnvironment>;
  validation: RuntimeValidationSummary;
  initialized: boolean;
  startupTime: Date;
}

let configurationInstance: SecureConfiguration | null = null;

/**
 * Initializes the secure configuration system
 * This should be called once during application startup
 */
export async function initializeSecureConfiguration(options: {
  throwOnCritical?: boolean;
  enableAuditLogging?: boolean;
} = {}): Promise<SecureConfiguration> {
  const { throwOnCritical = true, enableAuditLogging = true } = options;
  
  console.log('🔐 Initializing secure configuration system...');
  
  try {
    // Enable audit logging
    if (enableAuditLogging) {
      auditLogger.setEnabled(true);
    }
    
    // Validate environment configuration
    const environment = getValidatedEnvironment();
    
    // Perform runtime validation
    const validation = await validateOnStartup(throwOnCritical);
    
    // Log successful startup validation
    auditLogger.logStartupValidation(validation.results.map(r => ({
      component: r.component,
      checkName: r.checkName,
      success: r.success,
      severity: r.severity,
      message: r.message,
    })));
    
    configurationInstance = {
      environment,
      validation,
      initialized: true,
      startupTime: new Date(),
    };
    
    console.log('✅ Secure configuration system initialized successfully');
    
    return configurationInstance;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    auditLogger.logSecurityEvent('configuration_initialization_failed', {
      error: errorMessage,
    }, 'critical');
    
    console.error('🚨 Failed to initialize secure configuration system:', errorMessage);
    throw error;
  }
}

/**
 * Gets the current secure configuration
 * Throws an error if configuration hasn't been initialized
 */
export function getSecureConfiguration(): SecureConfiguration {
  if (!configurationInstance) {
    throw new Error('Secure configuration has not been initialized. Call initializeSecureConfiguration() first.');
  }
  
  return configurationInstance;
}

/**
 * Checks if the secure configuration system is initialized
 */
export function isConfigurationInitialized(): boolean {
  return configurationInstance !== null && configurationInstance.initialized;
}

/**
 * Re-validates the configuration (useful for health checks)
 */
export async function revalidateConfiguration(): Promise<RuntimeValidationSummary> {
  if (!configurationInstance) {
    throw new Error('Configuration not initialized');
  }
  
  const { performRuntimeValidation } = await import('./runtime-validation');
  const validation = await performRuntimeValidation();
  
  configurationInstance.validation = validation;
  
  return validation;
}

/**
 * Gets configuration health status
 */
export function getConfigurationHealth(): {
  status: 'healthy' | 'degraded' | 'unhealthy';
  issues: string[];
  lastCheck: Date;
} {
  if (!configurationInstance) {
    return {
      status: 'unhealthy',
      issues: ['Configuration not initialized'],
      lastCheck: new Date(),
    };
  }
  
  const { validation } = configurationInstance;
  const issues: string[] = [];
  
  if (validation.critical > 0) {
    issues.push(`${validation.critical} critical issues`);
  }
  if (validation.errors > 0) {
    issues.push(`${validation.errors} errors`);
  }
  if (validation.warnings > 0) {
    issues.push(`${validation.warnings} warnings`);
  }
  
  let status: 'healthy' | 'degraded' | 'unhealthy' = 'healthy';
  if (validation.critical > 0 || validation.errors > 0) {
    status = 'unhealthy';
  } else if (validation.warnings > 0) {
    status = 'degraded';
  }
  
  return {
    status,
    issues,
    lastCheck: new Date(),
  };
}

/**
 * Configuration utilities for Next.js
 */
export const nextjsConfig = {
  /**
   * Gets secure environment variables for Next.js config
   */
  getSecureEnvVars(): Record<string, string> {
    const config = getSecureConfiguration();
    return {
      NEXT_PUBLIC_APP_URL: config.environment.NEXT_PUBLIC_APP_URL,
      // Only expose non-sensitive public variables
    };
  },
  
  /**
   * Gets security headers configuration
   */
  getSecurityHeaders(isDevelopment: boolean = false) {
    const config = getSecureConfiguration();
    
    const baseHeaders = [
      {
        key: 'X-DNS-Prefetch-Control',
        value: 'on',
      },
      {
        key: 'Strict-Transport-Security',
        value: 'max-age=63072000; includeSubDomains; preload',
      },
      {
        key: 'X-Frame-Options',
        value: 'SAMEORIGIN',
      },
      {
        key: 'X-Content-Type-Options',
        value: 'nosniff',
      },
      {
        key: 'X-XSS-Protection',
        value: '1; mode=block',
      },
      {
        key: 'Referrer-Policy',
        value: 'strict-origin-when-cross-origin',
      },
      {
        key: 'Permissions-Policy',
        value: 'camera=(), microphone=(), geolocation=()',
      },
    ];
    
    // Content Security Policy
    const cspDirectives = isDevelopment ? [
      "default-src 'self'",
      "script-src 'self' 'unsafe-eval'", // Required for Next.js dev
      "style-src 'self' 'unsafe-inline'", // Required for Carbon
      "img-src 'self' data: blob: https:",
      "font-src 'self' data:",
      "connect-src 'self' http://localhost:* ws://localhost:*",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ] : [
      "default-src 'self'",
      "script-src 'self'",
      "style-src 'self'",
      "img-src 'self' data: https:",
      "font-src 'self' data:",
      `connect-src 'self' ${config.environment.NEXT_PUBLIC_API_URL} wss://*.kyros-praxis.com https://*.kyros-praxis.com`,
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "upgrade-insecure-requests",
    ];
    
    return [
      ...baseHeaders,
      {
        key: 'Content-Security-Policy',
        value: cspDirectives.join('; '),
      },
    ];
  },
  
  /**
   * Gets secure redirects configuration
   */
  getSecureRedirects(isDevelopment: boolean = false) {
    if (isDevelopment) {
      return [];
    }
    
    return [
      {
        source: '/:path*',
        has: [
          {
            type: 'header',
            key: 'x-forwarded-proto',
            value: 'http',
          },
        ],
        destination: 'https://:host/:path*',
        permanent: true,
      },
    ];
  },
};