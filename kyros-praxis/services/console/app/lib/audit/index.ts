/**
 * Audit Logging System - Main Export Module
 */

// Core audit system
export {
  AuditLogger,
  auditLogger,
  AuditEventType,
  AuditSeverity,
  auditAuth,
  auditUserAction,
  auditDataAccess,
  auditAdminAction,
  auditSecurityIncident,
  type AuditLogEntry,
} from '../audit';

// React integration  
export {
  useAuditLogging,
  type UseAuditLoggingOptions,
} from '../../hooks/useAuditLogging';

// Component wrappers
export {
  AuditWrapper,
  withAuditLogging,
  useManualAuditLogging,
} from '../components/AuditWrapper';
