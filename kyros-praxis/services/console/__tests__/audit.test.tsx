/**
 * Tests for the audit logging system
 */

import { AuditLogger, AuditEventType, AuditSeverity } from '../app/lib/audit';

// Mock fetch globally
global.fetch = jest.fn();

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Create a test logger with console logging enabled
let testLogger: any;

describe('Audit Logging System', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ success: true }),
    });
    
    // Create test logger instance with console logging enabled
    testLogger = new (AuditLogger as any)({
      enabled: true,
      logToConsole: true,
      logToServer: false,
      bufferSize: 10,
    });
  });

  describe('auditLogger', () => {
    test('should generate unique IDs for log entries', async () => {
      const spy = jest.spyOn(console, 'log').mockImplementation();
      
      await testLogger.log(AuditEventType.USER_ACTION, {});
      await testLogger.log(AuditEventType.USER_ACTION, {});
      
      expect(spy).toHaveBeenCalledTimes(2);
      
      const calls = spy.mock.calls;
      const entry1 = calls[0][1];
      const entry2 = calls[1][1];
      
      expect(entry1.id).not.toBe(entry2.id);
      expect(entry1.id).toMatch(/^audit_\d+_\w+$/);
      
      spy.mockRestore();
    });

    test('should determine correct severity levels', async () => {
      const spy = jest.spyOn(console, 'log').mockImplementation();
      
      await testLogger.log(AuditEventType.SECURITY_UNAUTHORIZED_ACCESS);
      await testLogger.log(AuditEventType.ADMIN_USER_CREATE);
      await testLogger.log(AuditEventType.LOGIN_SUCCESS);
      await testLogger.log(AuditEventType.USER_ACTION);
      
      const calls = spy.mock.calls;
      expect(calls[0][1].severity).toBe(AuditSeverity.HIGH);
      expect(calls[1][1].severity).toBe(AuditSeverity.MEDIUM);
      expect(calls[2][1].severity).toBe(AuditSeverity.MEDIUM);
      expect(calls[3][1].severity).toBe(AuditSeverity.LOW);
      
      spy.mockRestore();
    });

    test('should include browser context when available', async () => {
      const spy = jest.spyOn(console, 'log').mockImplementation();
      
      // Mock window object
      Object.defineProperty(window, 'location', {
        value: { href: 'https://example.com/test' },
        configurable: true,
      });
      Object.defineProperty(document, 'referrer', {
        value: 'https://example.com/previous',
        configurable: true,
      });
      Object.defineProperty(window, 'innerWidth', { value: 1920, configurable: true });
      Object.defineProperty(window, 'innerHeight', { value: 1080, configurable: true });
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 Test Browser',
        configurable: true,
      });
      
      await testLogger.log(AuditEventType.USER_ACTION, {});
      
      const logEntry = spy.mock.calls[0][1];
      expect(logEntry.userAgent).toBe('Mozilla/5.0 Test Browser');
      expect(logEntry.metadata.url).toBe('https://example.com/test');
      expect(logEntry.metadata.referrer).toBe('https://example.com/previous');
      expect(logEntry.metadata.viewport).toBe('1920x1080');
      
      spy.mockRestore();
    });

    test('should flush logs to server', async () => {
      // Create a new logger with smaller buffer for testing
      const flushTestLogger = new (AuditLogger as any)({
        bufferSize: 2,
        flushInterval: 1000,
        logToServer: true,
        logToConsole: false,
      });
      
      await flushTestLogger.log(AuditEventType.USER_ACTION, {});
      await flushTestLogger.log(AuditEventType.USER_ACTION, {});
      
      // Buffer should be full and trigger flush
      expect(fetch).toHaveBeenCalledWith('/api/audit/logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: expect.stringContaining('audit_'),
      });
    });
  });

  describe('Authentication logging', () => {
    test('should log successful authentication', async () => {
      const spy = jest.spyOn(console, 'log').mockImplementation();
      
      await testLogger.logAuth(
        AuditEventType.LOGIN_SUCCESS,
        'user123',
        'user@example.com',
        true,
        undefined,
        { sessionId: 'session123' }
      );
      
      const logEntry = spy.mock.calls[0][1];
      expect(logEntry.eventType).toBe(AuditEventType.LOGIN_SUCCESS);
      expect(logEntry.userId).toBe('user123');
      expect(logEntry.userEmail).toBe('user@example.com');
      expect(logEntry.success).toBe(true);
      expect(logEntry.details.sessionId).toBe('session123');
      
      spy.mockRestore();
    });

    test('should log failed authentication with error message', async () => {
      const spy = jest.spyOn(console, 'log').mockImplementation();
      
      await testLogger.logAuth(
        AuditEventType.LOGIN_FAILURE,
        undefined,
        'user@example.com',
        false,
        'Invalid credentials'
      );
      
      const logEntry = spy.mock.calls[0][1];
      expect(logEntry.eventType).toBe(AuditEventType.LOGIN_FAILURE);
      expect(logEntry.userId).toBeUndefined();
      expect(logEntry.userEmail).toBe('user@example.com');
      expect(logEntry.success).toBe(false);
      expect(logEntry.errorMessage).toBe('Invalid credentials');
      
      spy.mockRestore();
    });
  });

  describe('Data access logging', () => {
    test('should log data operations correctly', async () => {
      const spy = jest.spyOn(console, 'log').mockImplementation();
      
      await testLogger.logDataAccess(
        'create',
        'users',
        'user123',
        { recordId: 'new-user-456' }
      );
      
      const logEntry = spy.mock.calls[0][1];
      expect(logEntry.eventType).toBe(AuditEventType.DATA_CREATE);
      expect(logEntry.userId).toBe('user123');
      expect(logEntry.resource).toBe('users');
      expect(logEntry.action).toBe('create');
      expect(logEntry.details.recordId).toBe('new-user-456');
      
      spy.mockRestore();
    });
  });

  describe('Security incident logging', () => {
    test('should log security incidents with high severity', async () => {
      const spy = jest.spyOn(console, 'log').mockImplementation();
      
      await testLogger.logSecurityIncident(
        AuditEventType.SECURITY_UNAUTHORIZED_ACCESS,
        AuditSeverity.CRITICAL,
        'user123',
        { attemptedResource: '/admin/users' },
        'User attempted to access restricted area'
      );
      
      const logEntry = spy.mock.calls[0][1];
      expect(logEntry.eventType).toBe(AuditEventType.SECURITY_UNAUTHORIZED_ACCESS);
      expect(logEntry.severity).toBe(AuditSeverity.CRITICAL);
      expect(logEntry.userId).toBe('user123');
      expect(logEntry.success).toBe(false);
      expect(logEntry.errorMessage).toBe('User attempted to access restricted area');
      expect(logEntry.details.isSecurityIncident).toBe(true);
      expect(logEntry.details.attemptedResource).toBe('/admin/users');
      
      spy.mockRestore();
    });
  });

  describe('Admin action logging', () => {
    test('should log admin actions with proper context', async () => {
      const spy = jest.spyOn(console, 'log').mockImplementation();
      
      await testLogger.logAdminAction(
        'user_delete',
        'users',
        'admin123',
        'target456',
        { reason: 'Policy violation' }
      );
      
      const logEntry = spy.mock.calls[0][1];
      expect(logEntry.eventType).toBe(AuditEventType.ADMIN_SYSTEM_ACTION);
      expect(logEntry.userId).toBe('admin123');
      expect(logEntry.action).toBe('user_delete');
      expect(logEntry.resource).toBe('users');
      expect(logEntry.details.isAdminAction).toBe(true);
      expect(logEntry.details.targetUserId).toBe('target456');
      expect(logEntry.details.reason).toBe('Policy violation');
      
      spy.mockRestore();
    });
  });

  describe('Configuration', () => {
    test('should respect disabled configuration', async () => {
      const disabledLogger = new (AuditLogger as any)({
        enabled: false,
      });
      
      const spy = jest.spyOn(console, 'log').mockImplementation();
      
      await disabledLogger.log(AuditEventType.USER_ACTION, {});
      
      expect(spy).not.toHaveBeenCalled();
      spy.mockRestore();
    });

    test('should respect console logging configuration', async () => {
      const noConsoleLogger = new (AuditLogger as any)({
        logToConsole: false,
      });
      
      const spy = jest.spyOn(console, 'log').mockImplementation();
      
      await noConsoleLogger.log(AuditEventType.USER_ACTION, {});
      
      expect(spy).not.toHaveBeenCalled();
      spy.mockRestore();
    });
  });

  describe('Error handling', () => {
    test('should handle fetch errors gracefully', async () => {
      (fetch as jest.Mock).mockRejectedValue(new Error('Network error'));
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      
      await testLogger.flush();
      
      // Should not throw, but may log error
      // Note: The error might not always be logged depending on buffer state
      
      consoleErrorSpy.mockRestore();
    });
  });
});