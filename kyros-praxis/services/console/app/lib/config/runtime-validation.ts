import { validateEnvironment, isSecureForProduction } from './env-validation';
import { validateSecretStrength, getEnvironmentSecret } from './secrets';

/**
 * Runtime Configuration Validation
 * 
 * This module provides runtime validation checks that are performed during
 * application startup and periodically during runtime to ensure configuration
 * remains secure and valid.
 */

export interface ValidationResult {
  success: boolean;
  component: string;
  checkName: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  details?: Record<string, any>;
  timestamp: Date;
}

export interface RuntimeValidationSummary {
  overall: 'healthy' | 'warnings' | 'errors' | 'critical';
  totalChecks: number;
  passed: number;
  warnings: number;
  errors: number;
  critical: number;
  results: ValidationResult[];
  duration: number; // in milliseconds
}

/**
 * Performs comprehensive runtime validation of the application configuration
 */
export async function performRuntimeValidation(): Promise<RuntimeValidationSummary> {
  const startTime = Date.now();
  const results: ValidationResult[] = [];
  
  console.log('🔍 Starting runtime configuration validation...');
  
  // Environment validation
  results.push(...await validateEnvironmentConfiguration());
  
  // Security configuration validation
  results.push(...await validateSecurityConfiguration());
  
  // External service connectivity validation
  results.push(...await validateExternalServices());
  
  // NextAuth configuration validation
  results.push(...await validateNextAuthConfiguration());
  
  // Production readiness validation
  if (process.env.NODE_ENV === 'production') {
    results.push(...await validateProductionReadiness());
  }
  
  const duration = Date.now() - startTime;
  const summary = createValidationSummary(results, duration);
  
  logValidationSummary(summary);
  
  return summary;
}

/**
 * Validates environment configuration
 */
async function validateEnvironmentConfiguration(): Promise<ValidationResult[]> {
  const results: ValidationResult[] = [];
  
  try {
    const envValidation = validateEnvironment();
    
    if (envValidation.success) {
      results.push({
        success: true,
        component: 'environment',
        checkName: 'env_validation',
        severity: 'info',
        message: 'Environment variables validation passed',
        timestamp: new Date(),
      });
      
      // Check for warnings
      if (envValidation.warnings && envValidation.warnings.length > 0) {
        results.push({
          success: true,
          component: 'environment',
          checkName: 'env_warnings',
          severity: 'warning',
          message: 'Environment configuration has warnings',
          details: { warnings: envValidation.warnings },
          timestamp: new Date(),
        });
      }
    } else {
      results.push({
        success: false,
        component: 'environment',
        checkName: 'env_validation',
        severity: 'critical',
        message: 'Environment variables validation failed',
        details: { errors: envValidation.errors },
        timestamp: new Date(),
      });
    }
  } catch (error) {
    results.push({
      success: false,
      component: 'environment',
      checkName: 'env_validation',
      severity: 'critical',
      message: `Environment validation error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      timestamp: new Date(),
    });
  }
  
  return results;
}

/**
 * Validates security configuration
 */
async function validateSecurityConfiguration(): Promise<ValidationResult[]> {
  const results: ValidationResult[] = [];
  
  // Validate NEXTAUTH_SECRET
  try {
    const nextAuthSecret = getEnvironmentSecret('NEXTAUTH_SECRET', true);
    if (nextAuthSecret) {
      const secretValidation = validateSecretStrength(nextAuthSecret);
      
      if (secretValidation.valid) {
        results.push({
          success: true,
          component: 'security',
          checkName: 'nextauth_secret_strength',
          severity: 'info',
          message: `NEXTAUTH_SECRET validation passed (score: ${secretValidation.score}/100)`,
          details: { score: secretValidation.score },
          timestamp: new Date(),
        });
      } else {
        results.push({
          success: false,
          component: 'security',
          checkName: 'nextauth_secret_strength',
          severity: 'error',
          message: 'NEXTAUTH_SECRET failed security validation',
          details: { 
            issues: secretValidation.issues,
            recommendations: secretValidation.recommendations 
          },
          timestamp: new Date(),
        });
      }
    }
  } catch (error) {
    results.push({
      success: false,
      component: 'security',
      checkName: 'nextauth_secret_presence',
      severity: 'critical',
      message: 'NEXTAUTH_SECRET is not configured',
      timestamp: new Date(),
    });
  }
  
  // Check for development bypasses in production
  if (process.env.NODE_ENV === 'production') {
    const devLogin = process.env.NEXT_PUBLIC_ALLOW_DEV_LOGIN;
    if (devLogin === 'true') {
      results.push({
        success: false,
        component: 'security',
        checkName: 'dev_bypass_disabled',
        severity: 'critical',
        message: 'Development login bypass is enabled in production',
        timestamp: new Date(),
      });
    } else {
      results.push({
        success: true,
        component: 'security',
        checkName: 'dev_bypass_disabled',
        severity: 'info',
        message: 'Development login bypass is properly disabled',
        timestamp: new Date(),
      });
    }
  }
  
  return results;
}

/**
 * Validates external service connectivity
 */
async function validateExternalServices(): Promise<ValidationResult[]> {
  const results: ValidationResult[] = [];
  
  // Test API connectivity
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (apiUrl) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
      
      const response = await fetch(`${apiUrl}/utils/health-check`, {
        signal: controller.signal,
        headers: {
          'User-Agent': 'Console-Runtime-Validation/1.0',
        },
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        results.push({
          success: true,
          component: 'connectivity',
          checkName: 'api_health_check',
          severity: 'info',
          message: 'API health check passed',
          details: { status: response.status, url: apiUrl },
          timestamp: new Date(),
        });
      } else {
        results.push({
          success: false,
          component: 'connectivity',
          checkName: 'api_health_check',
          severity: 'error',
          message: `API health check failed with status ${response.status}`,
          details: { status: response.status, url: apiUrl },
          timestamp: new Date(),
        });
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      const severity = errorMessage.includes('abort') ? 'warning' : 'error';
      
      results.push({
        success: false,
        component: 'connectivity',
        checkName: 'api_health_check',
        severity,
        message: `API connectivity test failed: ${errorMessage}`,
        details: { url: apiUrl, error: errorMessage },
        timestamp: new Date(),
      });
    }
  }
  
  return results;
}

/**
 * Validates NextAuth configuration
 */
async function validateNextAuthConfiguration(): Promise<ValidationResult[]> {
  const results: ValidationResult[] = [];
  
  // Check NextAuth URL configuration
  const nextAuthUrl = process.env.NEXTAUTH_URL || process.env.NEXT_PUBLIC_APP_URL;
  if (nextAuthUrl) {
    try {
      const url = new URL(nextAuthUrl);
      
      if (process.env.NODE_ENV === 'production' && url.protocol !== 'https:') {
        results.push({
          success: false,
          component: 'nextauth',
          checkName: 'nextauth_url_secure',
          severity: 'error',
          message: 'NEXTAUTH_URL must use HTTPS in production',
          details: { url: nextAuthUrl },
          timestamp: new Date(),
        });
      } else {
        results.push({
          success: true,
          component: 'nextauth',
          checkName: 'nextauth_url_valid',
          severity: 'info',
          message: 'NextAuth URL configuration is valid',
          timestamp: new Date(),
        });
      }
    } catch (error) {
      results.push({
        success: false,
        component: 'nextauth',
        checkName: 'nextauth_url_valid',
        severity: 'error',
        message: 'NextAuth URL is not a valid URL',
        details: { url: nextAuthUrl },
        timestamp: new Date(),
      });
    }
  }
  
  return results;
}

/**
 * Validates production readiness
 */
async function validateProductionReadiness(): Promise<ValidationResult[]> {
  const results: ValidationResult[] = [];
  
  const productionCheck = isSecureForProduction();
  
  if (productionCheck.secure) {
    results.push({
      success: true,
      component: 'production',
      checkName: 'production_readiness',
      severity: 'info',
      message: 'Application is secure for production deployment',
      timestamp: new Date(),
    });
  } else {
    results.push({
      success: false,
      component: 'production',
      checkName: 'production_readiness',
      severity: 'critical',
      message: 'Application has production security issues',
      details: { issues: productionCheck.issues },
      timestamp: new Date(),
    });
  }
  
  // Check for Sentry configuration in production
  if (!process.env.SENTRY_DSN) {
    results.push({
      success: false,
      component: 'production',
      checkName: 'sentry_monitoring',
      severity: 'warning',
      message: 'Sentry monitoring is not configured for production error tracking',
      timestamp: new Date(),
    });
  }
  
  return results;
}

/**
 * Creates a summary of validation results
 */
function createValidationSummary(results: ValidationResult[], duration: number): RuntimeValidationSummary {
  const passed = results.filter(r => r.success).length;
  const warnings = results.filter(r => !r.success && r.severity === 'warning').length;
  const errors = results.filter(r => !r.success && r.severity === 'error').length;
  const critical = results.filter(r => !r.success && r.severity === 'critical').length;
  
  let overall: RuntimeValidationSummary['overall'] = 'healthy';
  if (critical > 0) {
    overall = 'critical';
  } else if (errors > 0) {
    overall = 'errors';
  } else if (warnings > 0) {
    overall = 'warnings';
  }
  
  return {
    overall,
    totalChecks: results.length,
    passed,
    warnings,
    errors,
    critical,
    results,
    duration,
  };
}

/**
 * Logs the validation summary
 */
function logValidationSummary(summary: RuntimeValidationSummary): void {
  const emoji = {
    healthy: '✅',
    warnings: '⚠️',
    errors: '❌',
    critical: '🚨',
  };
  
  console.log(`${emoji[summary.overall]} Runtime validation completed in ${summary.duration}ms`);
  console.log(`📊 Results: ${summary.passed} passed, ${summary.warnings} warnings, ${summary.errors} errors, ${summary.critical} critical`);
  
  // Log critical and error issues
  const criticalIssues = summary.results.filter(r => !r.success && r.severity === 'critical');
  const errorIssues = summary.results.filter(r => !r.success && r.severity === 'error');
  
  if (criticalIssues.length > 0) {
    console.error('🚨 Critical Issues:');
    criticalIssues.forEach(issue => {
      console.error(`  • ${issue.component}.${issue.checkName}: ${issue.message}`);
    });
  }
  
  if (errorIssues.length > 0) {
    console.error('❌ Errors:');
    errorIssues.forEach(issue => {
      console.error(`  • ${issue.component}.${issue.checkName}: ${issue.message}`);
    });
  }
  
  const warningIssues = summary.results.filter(r => !r.success && r.severity === 'warning');
  if (warningIssues.length > 0) {
    console.warn('⚠️  Warnings:');
    warningIssues.forEach(issue => {
      console.warn(`  • ${issue.component}.${issue.checkName}: ${issue.message}`);
    });
  }
}

/**
 * Validates configuration on startup and optionally throws on critical issues
 */
export async function validateOnStartup(throwOnCritical: boolean = true): Promise<RuntimeValidationSummary> {
  const summary = await performRuntimeValidation();
  
  if (throwOnCritical && summary.critical > 0) {
    const criticalIssues = summary.results
      .filter(r => !r.success && r.severity === 'critical')
      .map(r => r.message)
      .join('\n');
    
    throw new Error(`Critical configuration issues prevent startup:\n${criticalIssues}`);
  }
  
  return summary;
}