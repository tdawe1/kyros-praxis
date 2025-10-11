import { NextRequest, NextResponse } from 'next/server';
import { 
  getConfigurationHealth, 
  isConfigurationInitialized,
  revalidateConfiguration 
} from '../../../lib/config';

/**
 * Configuration Health Check API
 * 
 * Provides health status information about the application's configuration
 * without exposing sensitive configuration details.
 */

export async function GET(request: NextRequest) {
  try {
    // Check if configuration system is initialized
    if (!isConfigurationInitialized()) {
      return NextResponse.json({
        status: 'error',
        message: 'Configuration system not initialized',
        timestamp: new Date().toISOString(),
      }, { status: 503 });
    }

    // Get current health status
    const health = getConfigurationHealth();
    
    // Determine HTTP status code based on health
    let statusCode = 200;
    if (health.status === 'unhealthy') {
      statusCode = 503; // Service Unavailable
    } else if (health.status === 'degraded') {
      statusCode = 200; // OK but with warnings
    }

    return NextResponse.json({
      status: health.status,
      issues: health.issues,
      lastCheck: health.lastCheck,
      timestamp: new Date().toISOString(),
    }, { status: statusCode });

  } catch (error) {
    console.error('Configuration health check failed:', error);
    
    return NextResponse.json({
      status: 'error',
      message: 'Configuration health check failed',
      timestamp: new Date().toISOString(),
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    // Trigger configuration revalidation
    const validation = await revalidateConfiguration();
    
    const health = getConfigurationHealth();
    
    return NextResponse.json({
      status: 'revalidated',
      health: {
        status: health.status,
        issues: health.issues,
        lastCheck: health.lastCheck,
      },
      validation: {
        overall: validation.overall,
        totalChecks: validation.totalChecks,
        passed: validation.passed,
        warnings: validation.warnings,
        errors: validation.errors,
        critical: validation.critical,
        duration: validation.duration,
      },
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('Configuration revalidation failed:', error);
    
    return NextResponse.json({
      status: 'error',
      message: 'Configuration revalidation failed',
      timestamp: new Date().toISOString(),
    }, { status: 500 });
  }
}