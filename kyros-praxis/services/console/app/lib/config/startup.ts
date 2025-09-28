/**
 * Application Startup Configuration
 * 
 * This module handles the initialization of secure configuration during
 * application startup, ensuring all security checks pass before the
 * application becomes available.
 */

import { initializeSecureConfiguration, getConfigurationHealth } from './index';

/**
 * Initialize secure configuration on application startup
 * This should be called early in the application lifecycle
 */
export async function initializeOnStartup(): Promise<void> {
  try {
    console.log('🚀 Starting secure configuration initialization...');
    
    await initializeSecureConfiguration({
      throwOnCritical: process.env.NODE_ENV === 'production',
      enableAuditLogging: true,
    });
    
    // Log configuration health status
    const health = getConfigurationHealth();
    if (health.status === 'healthy') {
      console.log('✅ Configuration health: All systems operational');
    } else {
      console.warn(`⚠️  Configuration health: ${health.status}`, health.issues);
    }
    
  } catch (error) {
    console.error('🚨 Failed to initialize secure configuration:', error);
    
    if (process.env.NODE_ENV === 'production') {
      // In production, we should not start if configuration is invalid
      process.exit(1);
    } else {
      // In development, log the error but continue
      console.warn('⚠️  Continuing with default configuration in development mode');
    }
  }
}

/**
 * Runtime configuration check middleware for Next.js API routes
 */
export function withConfigurationCheck<T extends (...args: any[]) => any>(handler: T): T {
  return (async (...args: any[]) => {
    try {
      const health = getConfigurationHealth();
      
      if (health.status === 'unhealthy') {
        // Return configuration error
        const [, res] = args; // Assume Next.js API route format
        if (res && typeof res.status === 'function') {
          return res.status(503).json({
            error: 'Service configuration is unhealthy',
            issues: health.issues,
          });
        }
      }
      
      return await handler(...args);
    } catch (error) {
      console.error('Configuration check failed:', error);
      
      // Continue with handler in development, fail in production
      if (process.env.NODE_ENV === 'production') {
        const [, res] = args;
        if (res && typeof res.status === 'function') {
          return res.status(503).json({
            error: 'Service configuration error',
          });
        }
      }
      
      return await handler(...args);
    }
  }) as T;
}