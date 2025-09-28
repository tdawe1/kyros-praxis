import { createHash } from 'crypto';
import { appendAudit, AuditEntry } from '../server/devlogs';

/**
 * Configuration Audit Logging
 * 
 * This module provides comprehensive audit logging for configuration changes,
 * secret access, and security-related events to maintain a complete audit trail.
 */

export interface ConfigurationAuditEvent {
  type: 'config_change' | 'secret_access' | 'validation_failure' | 'security_event';
  component: string;
  action: string;
  resource?: string;
  oldValue?: string; // Hashed for sensitive data
  newValue?: string; // Hashed for sensitive data
  user?: string;
  source: 'system' | 'user' | 'api' | 'startup';
  severity: 'info' | 'warning' | 'error' | 'critical';
  metadata?: Record<string, any>;
  timestamp: Date;
  sessionId?: string;
  requestId?: string;
}

export interface AuditLogQuery {
  type?: ConfigurationAuditEvent['type'];
  component?: string;
  severity?: ConfigurationAuditEvent['severity'];
  source?: ConfigurationAuditEvent['source'];
  fromDate?: Date;
  toDate?: Date;
  limit?: number;
}

/**
 * Audit logger for configuration changes
 */
export class ConfigurationAuditLogger {
  private static instance: ConfigurationAuditLogger;
  private enabled: boolean;
  
  private constructor() {
    this.enabled = process.env.NODE_ENV !== 'test';
  }
  
  static getInstance(): ConfigurationAuditLogger {
    if (!ConfigurationAuditLogger.instance) {
      ConfigurationAuditLogger.instance = new ConfigurationAuditLogger();
    }
    return ConfigurationAuditLogger.instance;
  }
  
  /**
   * Logs a configuration audit event
   */
  logEvent(event: Omit<ConfigurationAuditEvent, 'timestamp'>): void {
    if (!this.enabled) return;
    
    const auditEvent: ConfigurationAuditEvent = {
      ...event,
      timestamp: new Date(),
    };
    
    // Hash sensitive values
    if (auditEvent.oldValue) {
      auditEvent.oldValue = this.hashSensitiveValue(auditEvent.oldValue);
    }
    if (auditEvent.newValue) {
      auditEvent.newValue = this.hashSensitiveValue(auditEvent.newValue);
    }
    
    // Convert to AuditEntry format for devlogs
    const auditEntry: AuditEntry = {
      ts: auditEvent.timestamp.toISOString(),
      action: this.mapActionToAuditAction(auditEvent.action),
      targets: [auditEvent.component],
      mode: auditEvent.type,
      summary: this.createEventSummary(auditEvent),
      payload_hash: this.hashEvent(auditEvent),
    };
    
    // Log to devlogs system
    appendAudit(auditEntry);
    
    // Also log to console based on severity
    this.logToConsole(auditEvent);
  }
  
  /**
   * Logs configuration validation failures
   */
  logValidationFailure(
    component: string,
    validationName: string,
    errors: string[],
    severity: 'warning' | 'error' | 'critical' = 'error'
  ): void {
    this.logEvent({
      type: 'validation_failure',
      component,
      action: 'validation_failed',
      resource: validationName,
      source: 'system',
      severity,
      metadata: { errors },
    });
  }
  
  /**
   * Logs secret access events
   */
  logSecretAccess(
    secretId: string,
    action: 'read' | 'write' | 'delete',
    user?: string,
    source: ConfigurationAuditEvent['source'] = 'system'
  ): void {
    this.logEvent({
      type: 'secret_access',
      component: 'secrets',
      action: `secret_${action}`,
      resource: secretId,
      user,
      source,
      severity: 'info',
    });
  }
  
  /**
   * Logs environment configuration changes
   */
  logEnvironmentChange(
    variable: string,
    oldValue?: string,
    newValue?: string,
    source: ConfigurationAuditEvent['source'] = 'user'
  ): void {
    this.logEvent({
      type: 'config_change',
      component: 'environment',
      action: 'env_var_changed',
      resource: variable,
      oldValue,
      newValue,
      source,
      severity: this.isSensitiveEnvironmentVariable(variable) ? 'warning' : 'info',
    });
  }
  
  /**
   * Logs security-related events
   */
  logSecurityEvent(
    event: string,
    details: Record<string, any>,
    severity: ConfigurationAuditEvent['severity'] = 'warning'
  ): void {
    this.logEvent({
      type: 'security_event',
      component: 'security',
      action: event,
      source: 'system',
      severity,
      metadata: details,
    });
  }
  
  /**
   * Logs startup validation results
   */
  logStartupValidation(
    validationResults: Array<{
      component: string;
      checkName: string;
      success: boolean;
      severity: string;
      message: string;
    }>
  ): void {
    const failedChecks = validationResults.filter(r => !r.success);
    
    if (failedChecks.length > 0) {
      this.logEvent({
        type: 'validation_failure',
        component: 'startup',
        action: 'startup_validation',
        source: 'system',
        severity: failedChecks.some(c => c.severity === 'critical') ? 'critical' : 'warning',
        metadata: {
          totalChecks: validationResults.length,
          failedChecks: failedChecks.length,
          failures: failedChecks.map(c => ({
            component: c.component,
            check: c.checkName,
            message: c.message,
          })),
        },
      });
    } else {
      this.logEvent({
        type: 'security_event',
        component: 'startup',
        action: 'startup_validation_success',
        source: 'system',
        severity: 'info',
        metadata: {
          totalChecks: validationResults.length,
        },
      });
    }
  }
  
  /**
   * Retrieves audit logs based on query criteria
   */
  queryAuditLogs(query: AuditLogQuery = {}): ConfigurationAuditEvent[] {
    // This would typically integrate with a more sophisticated logging system
    // For now, we'll return an empty array as devlogs doesn't support complex queries
    console.warn('Audit log querying not fully implemented - consider integrating with external logging system');
    return [];
  }
  
  /**
   * Enables or disables audit logging
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
    this.logEvent({
      type: 'security_event',
      component: 'audit',
      action: enabled ? 'audit_enabled' : 'audit_disabled',
      source: 'system',
      severity: 'info',
    });
  }
  
  private mapActionToAuditAction(action: string): 'send' | 'escalate' | 'retry' | 'replay' {
    // Map configuration actions to supported audit actions
    if (action.includes('send') || action.includes('create') || action.includes('store')) {
      return 'send';
    }
    if (action.includes('escalate') || action.includes('critical') || action.includes('security')) {
      return 'escalate';
    }
    if (action.includes('retry') || action.includes('validate') || action.includes('check')) {
      return 'retry';
    }
    return 'replay'; // Default fallback
  }
  
  private hashSensitiveValue(value: string): string {
    // Only hash if the value looks sensitive
    if (this.isSensitiveValue(value)) {
      return createHash('sha256').update(value).digest('hex').substring(0, 16) + '...';
    }
    return value;
  }
  
  private isSensitiveValue(value: string): boolean {
    const sensitivePatterns = [
      /^[A-Za-z0-9+/]{20,}={0,2}$/, // Base64 encoded secrets
      /^[A-Fa-f0-9]{32,}$/, // Hex encoded secrets
      /password|secret|key|token/i, // Common secret keywords
    ];
    
    return sensitivePatterns.some(pattern => pattern.test(value)) || value.length > 50;
  }
  
  private isSensitiveEnvironmentVariable(variable: string): boolean {
    const sensitiveVars = [
      'NEXTAUTH_SECRET',
      'SENTRY_AUTH_TOKEN',
      'DATABASE_PASSWORD',
      'REDIS_PASSWORD',
      'API_KEY',
      'SECRET_KEY',
    ];
    
    return sensitiveVars.some(sensitiveVar => 
      variable.toUpperCase().includes(sensitiveVar.toUpperCase())
    );
  }
  
  private createEventSummary(event: ConfigurationAuditEvent): string {
    const parts = [event.component, event.action];
    if (event.resource) {
      parts.push(event.resource);
    }
    if (event.user) {
      parts.push(`by ${event.user}`);
    }
    return parts.join(' ');
  }
  
  private hashEvent(event: ConfigurationAuditEvent): string {
    const eventString = JSON.stringify({
      type: event.type,
      component: event.component,
      action: event.action,
      resource: event.resource,
      timestamp: event.timestamp.toISOString(),
    });
    return createHash('sha256').update(eventString).digest('hex').substring(0, 16);
  }
  
  private logToConsole(event: ConfigurationAuditEvent): void {
    const timestamp = event.timestamp.toISOString();
    const prefix = `[${timestamp}] [AUDIT] [${event.severity.toUpperCase()}]`;
    const message = `${prefix} ${event.component}.${event.action}`;
    
    switch (event.severity) {
      case 'critical':
        console.error(`🚨 ${message}`, event.metadata);
        break;
      case 'error':
        console.error(`❌ ${message}`, event.metadata);
        break;
      case 'warning':
        console.warn(`⚠️  ${message}`, event.metadata);
        break;
      case 'info':
        console.info(`ℹ️  ${message}`, event.metadata);
        break;
    }
  }
}

/**
 * Default audit logger instance
 */
export const auditLogger = ConfigurationAuditLogger.getInstance();

/**
 * Convenience functions for common audit events
 */
export const logConfigurationChange = (
  component: string,
  resource: string,
  oldValue?: string,
  newValue?: string,
  user?: string
) => auditLogger.logEvent({
  type: 'config_change',
  component,
  action: 'configuration_changed',
  resource,
  oldValue,
  newValue,
  user,
  source: user ? 'user' : 'system',
  severity: 'info',
});

export const logSecurityViolation = (
  component: string,
  violation: string,
  details: Record<string, any>
) => auditLogger.logSecurityEvent(`security_violation_${violation}`, {
  component,
  ...details,
}, 'critical');

export const logValidationSuccess = (
  component: string,
  validationType: string,
  checksCount: number
) => auditLogger.logEvent({
  type: 'security_event',
  component,
  action: `validation_success_${validationType}`,
  source: 'system',
  severity: 'info',
  metadata: { checksCount },
});