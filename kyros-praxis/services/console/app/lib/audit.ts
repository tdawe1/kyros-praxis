/**
 * Comprehensive Audit Logging System for Console Service
 * 
 * This module provides centralized audit logging capabilities including:
 * - User action logging
 * - Authentication events tracking  
 * - Security incident logging
 * - Data access logging
 * - Admin actions tracking
 */

// Audit log event types
export enum AuditEventType {
  // Authentication events
  LOGIN_ATTEMPT = 'auth.login.attempt',
  LOGIN_SUCCESS = 'auth.login.success',
  LOGIN_FAILURE = 'auth.login.failure', 
  LOGOUT = 'auth.logout',
  TOKEN_REFRESH = 'auth.token.refresh',
  SESSION_EXPIRED = 'auth.session.expired',

  // User actions
  USER_ACTION = 'user.action',
  PAGE_VIEW = 'user.page.view',
  FORM_SUBMIT = 'user.form.submit',
  BUTTON_CLICK = 'user.button.click',

  // Data access
  DATA_READ = 'data.read',
  DATA_CREATE = 'data.create', 
  DATA_UPDATE = 'data.update',
  DATA_DELETE = 'data.delete',
  DATA_EXPORT = 'data.export',

  // Admin actions
  ADMIN_USER_CREATE = 'admin.user.create',
  ADMIN_USER_UPDATE = 'admin.user.update',
  ADMIN_USER_DELETE = 'admin.user.delete',
  ADMIN_SETTINGS_UPDATE = 'admin.settings.update',
  ADMIN_SYSTEM_ACTION = 'admin.system.action',

  // Security incidents
  SECURITY_UNAUTHORIZED_ACCESS = 'security.unauthorized.access',
  SECURITY_SUSPICIOUS_ACTIVITY = 'security.suspicious.activity',
  SECURITY_RATE_LIMIT_EXCEEDED = 'security.rate_limit.exceeded',
  SECURITY_INVALID_TOKEN = 'security.invalid.token',
  SECURITY_PERMISSION_DENIED = 'security.permission.denied',
}

// Severity levels for audit events
export enum AuditSeverity {
  LOW = 'low',
  MEDIUM = 'medium', 
  HIGH = 'high',
  CRITICAL = 'critical'
}

// Core audit log entry interface
export interface AuditLogEntry {
  id: string;
  timestamp: string;
  eventType: AuditEventType;
  severity: AuditSeverity;
  userId?: string;
  userEmail?: string;
  sessionId?: string;
  ipAddress?: string;
  userAgent?: string;
  resource?: string;
  action?: string;
  details?: Record<string, any>;
  metadata?: Record<string, any>;
  success: boolean;
  errorMessage?: string;
}

// Configuration for audit logging
interface AuditConfig {
  enabled: boolean;
  logToConsole: boolean;
  logToServer: boolean;
  bufferSize: number;
  flushInterval: number;
  includeStackTrace: boolean;
}

export class AuditLogger {
  private config: AuditConfig;
  private logBuffer: AuditLogEntry[] = [];
  private flushTimer?: NodeJS.Timeout;

  constructor(config: Partial<AuditConfig> = {}) {
    this.config = {
      enabled: true,
      logToConsole: process.env.NODE_ENV === 'development',
      logToServer: true,
      bufferSize: 100,
      flushInterval: 30000, // 30 seconds
      includeStackTrace: false,
      ...config
    };

    if (this.config.enabled && this.config.logToServer) {
      this.startPeriodicFlush();
    }
  }

  /**
   * Log an audit event
   */
  async log(
    eventType: AuditEventType,
    details: Partial<AuditLogEntry> = {}
  ): Promise<void> {
    if (!this.config.enabled) return;

    const entry: AuditLogEntry = {
      id: this.generateId(),
      timestamp: new Date().toISOString(),
      eventType,
      severity: this.determineSeverity(eventType),
      success: true,
      ...details,
      // Get browser context if available
      ...(typeof window !== 'undefined' ? this.getBrowserContext() : {}),
    };

    // Add stack trace if configured
    if (this.config.includeStackTrace) {
      entry.metadata = {
        ...entry.metadata,
        stackTrace: new Error().stack
      };
    }

    // Log to console in development
    if (this.config.logToConsole) {
      console.log('[AUDIT]', entry);
    }

    // Add to buffer for server logging
    if (this.config.logToServer) {
      this.logBuffer.push(entry);
      
      // Flush if buffer is full
      if (this.logBuffer.length >= this.config.bufferSize) {
        await this.flush();
      }
    }
  }

  /**
   * Log authentication events
   */
  async logAuth(
    eventType: AuditEventType,
    userId?: string,
    userEmail?: string,
    success = true,
    errorMessage?: string,
    additionalDetails?: Record<string, any>
  ): Promise<void> {
    await this.log(eventType, {
      userId,
      userEmail,
      success,
      errorMessage,
      details: additionalDetails,
    });
  }

  /**
   * Log user actions
   */
  async logUserAction(
    action: string,
    resource?: string,
    userId?: string,
    details?: Record<string, any>
  ): Promise<void> {
    await this.log(AuditEventType.USER_ACTION, {
      userId,
      action,
      resource,
      details,
    });
  }

  /**
   * Log data access events
   */
  async logDataAccess(
    operation: 'read' | 'create' | 'update' | 'delete' | 'export',
    resource: string,
    userId?: string,
    details?: Record<string, any>
  ): Promise<void> {
    const eventTypeMap = {
      read: AuditEventType.DATA_READ,
      create: AuditEventType.DATA_CREATE,
      update: AuditEventType.DATA_UPDATE,
      delete: AuditEventType.DATA_DELETE,
      export: AuditEventType.DATA_EXPORT,
    };

    await this.log(eventTypeMap[operation], {
      userId,
      resource,
      action: operation,
      details,
    });
  }

  /**
   * Log admin actions
   */
  async logAdminAction(
    action: string,
    resource?: string,
    userId?: string,
    targetUserId?: string,
    details?: Record<string, any>
  ): Promise<void> {
    await this.log(AuditEventType.ADMIN_SYSTEM_ACTION, {
      userId,
      action,
      resource,
      details: {
        ...details,
        targetUserId,
        isAdminAction: true,
      },
    });
  }

  /**
   * Log security incidents
   */
  async logSecurityIncident(
    eventType: AuditEventType,
    severity: AuditSeverity,
    userId?: string,
    details?: Record<string, any>,
    errorMessage?: string
  ): Promise<void> {
    await this.log(eventType, {
      userId,
      severity,
      success: false,
      errorMessage,
      details: {
        ...details,
        isSecurityIncident: true,
      },
    });
  }

  /**
   * Flush logs to server immediately
   */
  async flush(): Promise<void> {
    if (this.logBuffer.length === 0) return;

    const logs = [...this.logBuffer];
    this.logBuffer = [];

    try {
      // Send logs to server endpoint
      if (typeof fetch !== 'undefined') {
        await fetch('/api/audit/logs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ logs }),
        });
      }
    } catch (error) {
      console.error('Failed to flush audit logs:', error);
      // Re-add logs to buffer for retry
      this.logBuffer.unshift(...logs);
    }
  }

  /**
   * Get browser context information
   */
  private getBrowserContext(): Partial<AuditLogEntry> {
    if (typeof window === 'undefined') return {};

    return {
      userAgent: navigator.userAgent,
      // Note: IP address should be captured server-side
      metadata: {
        url: window.location.href,
        referrer: document.referrer,
        viewport: `${window.innerWidth}x${window.innerHeight}`,
      },
    };
  }

  /**
   * Determine severity based on event type
   */
  private determineSeverity(eventType: AuditEventType): AuditSeverity {
    if (eventType.startsWith('security.')) {
      return AuditSeverity.HIGH;
    }
    if (eventType.startsWith('admin.')) {
      return AuditSeverity.MEDIUM;
    }
    if (eventType.startsWith('auth.')) {
      return AuditSeverity.MEDIUM;
    }
    return AuditSeverity.LOW;
  }

  /**
   * Generate unique ID for log entries
   */
  private generateId(): string {
    return `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Start periodic flushing of logs
   */
  private startPeriodicFlush(): void {
    this.flushTimer = setInterval(() => {
      this.flush().catch(console.error);
    }, this.config.flushInterval);
  }

  /**
   * Stop periodic flushing
   */
  destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }
    this.flush().catch(console.error);
  }
}

// Global audit logger instance
export const auditLogger = new AuditLogger({
  enabled: process.env.NEXT_PUBLIC_AUDIT_LOGGING_ENABLED !== 'false',
  logToConsole: process.env.NODE_ENV === 'development',
});

// Cleanup on page unload (browser only)
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    auditLogger.destroy();
  });
}

// Convenience functions for common audit operations
export const auditAuth = auditLogger.logAuth.bind(auditLogger);
export const auditUserAction = auditLogger.logUserAction.bind(auditLogger);
export const auditDataAccess = auditLogger.logDataAccess.bind(auditLogger);
export const auditAdminAction = auditLogger.logAdminAction.bind(auditLogger);
export const auditSecurityIncident = auditLogger.logSecurityIncident.bind(auditLogger);