/**
 * Comprehensive input sanitization utilities for preventing XSS and injection attacks
 */

import DOMPurify from 'isomorphic-dompurify';

/**
 * Configuration for different sanitization levels
 */
export const SANITIZATION_CONFIGS = {
  // Strict: Only allows basic text formatting
  strict: {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'u'],
    ALLOWED_ATTR: [],
    FORBID_CONTENTS: ['script', 'style', 'iframe', 'object', 'embed'],
    FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed', 'form', 'input'],
  },
  
  // Basic: Allows common formatting and links
  basic: {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'u', 'a', 'p', 'br', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href', 'title'],
    FORBID_CONTENTS: ['script', 'style', 'iframe', 'object', 'embed'],
    FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed', 'form', 'input'],
  },
  
  // Rich: Allows more HTML for rich text editors
  rich: {
    ALLOWED_TAGS: [
      'b', 'i', 'em', 'strong', 'u', 'a', 'p', 'br', 'ul', 'ol', 'li', 
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre',
      'table', 'thead', 'tbody', 'tr', 'td', 'th'
    ],
    ALLOWED_ATTR: ['href', 'title', 'alt', 'class'],
    FORBID_CONTENTS: ['script', 'style', 'iframe', 'object', 'embed'],
    FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed', 'form', 'input'],
  }
};

/**
 * Sanitize HTML content based on specified level
 */
export function sanitizeHtml(
  html: string, 
  level: keyof typeof SANITIZATION_CONFIGS = 'basic'
): string {
  if (!html || typeof html !== 'string') {
    return '';
  }

  const config = SANITIZATION_CONFIGS[level];
  return DOMPurify.sanitize(html, config);
}

/**
 * Sanitize plain text input by escaping HTML entities
 */
export function sanitizeText(text: string): string {
  if (!text || typeof text !== 'string') {
    return '';
  }

  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');
}

/**
 * Sanitize URL to prevent javascript: and data: schemes
 */
export function sanitizeUrl(url: string): string {
  if (!url || typeof url !== 'string') {
    return '';
  }

  // Remove any whitespace
  url = url.trim();

  // Check for dangerous protocols
  const dangerousProtocols = [
    'javascript:', 'data:', 'vbscript:', 'file:', 'about:',
    'chrome:', 'chrome-extension:', 'moz-extension:'
  ];

  const lowerUrl = url.toLowerCase();
  for (const protocol of dangerousProtocols) {
    if (lowerUrl.startsWith(protocol)) {
      return '';
    }
  }

  // Only allow http, https, mailto, tel, and relative URLs
  if (url.includes(':')) {
    const allowedProtocols = ['http:', 'https:', 'mailto:', 'tel:'];
    const hasAllowedProtocol = allowedProtocols.some(protocol => 
      lowerUrl.startsWith(protocol)
    );
    
    if (!hasAllowedProtocol) {
      return '';
    }
  }

  return url;
}

/**
 * Sanitize JSON input to prevent injection
 */
export function sanitizeJson(input: string): string {
  if (!input || typeof input !== 'string') {
    return '{}';
  }

  try {
    // Parse to validate JSON structure
    const parsed = JSON.parse(input);
    
    // Re-stringify to normalize and remove potential injections
    return JSON.stringify(parsed);
  } catch {
    // If invalid JSON, return empty object
    return '{}';
  }
}

/**
 * Sanitize file name to prevent path traversal and invalid characters
 */
export function sanitizeFileName(fileName: string): string {
  if (!fileName || typeof fileName !== 'string') {
    return '';
  }

  return fileName
    // Replace path traversal attempts
    .replace(/\.\./g, '')
    .replace(/[\/\\]/g, '')
    // Remove control characters and other dangerous chars
    .replace(/[\x00-\x1f\x80-\x9f]/g, '')
    // Remove potentially dangerous characters
    .replace(/[<>:"|?*]/g, '')
    // Trim whitespace and dots
    .replace(/^\.+|\.+$/g, '')
    .trim()
    // Limit length
    .substring(0, 255);
}

/**
 * Validate and sanitize email address
 */
export function sanitizeEmail(email: string): string {
  if (!email || typeof email !== 'string') {
    return '';
  }

  // Basic email validation and sanitization
  const sanitized = email.trim().toLowerCase();
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  
  return emailRegex.test(sanitized) ? sanitized : '';
}

/**
 * Sanitize search query to prevent injection attacks
 */
export function sanitizeSearchQuery(query: string): string {
  if (!query || typeof query !== 'string') {
    return '';
  }

  return query
    // Remove SQL injection patterns
    .replace(/(['";\\]|--|\*|\|)/g, '')
    // Remove script tags and similar (more comprehensive)
    .replace(/<script[^>]*>.*?<\/script>/gi, '')
    .replace(/<[^>]*>/g, '')
    // Remove JavaScript-like patterns
    .replace(/javascript\s*:/gi, '')
    .replace(/on\w+\s*=/gi, '')
    // Limit length
    .substring(0, 1000)
    .trim();
}

/**
 * Sanitize form data object recursively
 */
export function sanitizeFormData(data: Record<string, any>): Record<string, any> {
  if (!data || typeof data !== 'object') {
    return {};
  }

  const sanitized: Record<string, any> = {};

  for (const [key, value] of Object.entries(data)) {
    const sanitizedKey = sanitizeText(key);
    
    if (typeof value === 'string') {
      sanitized[sanitizedKey] = sanitizeText(value);
    } else if (typeof value === 'number' || typeof value === 'boolean') {
      sanitized[sanitizedKey] = value;
    } else if (Array.isArray(value)) {
      sanitized[sanitizedKey] = value.map(item => 
        typeof item === 'string' ? sanitizeText(item) : item
      );
    } else if (value && typeof value === 'object') {
      sanitized[sanitizedKey] = sanitizeFormData(value);
    } else {
      sanitized[sanitizedKey] = null;
    }
  }

  return sanitized;
}

/**
 * Validate file upload based on type and size
 */
export interface FileValidationResult {
  isValid: boolean;
  error?: string;
  sanitizedName?: string;
}

export function validateFileUpload(
  file: File,
  options: {
    allowedTypes?: string[];
    maxSize?: number; // in bytes
    allowedExtensions?: string[];
  } = {}
): FileValidationResult {
  const {
    allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'text/plain', 'application/pdf'],
    maxSize = 10 * 1024 * 1024, // 10MB default
    allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.txt', '.pdf']
  } = options;

  // Validate file type
  if (!allowedTypes.includes(file.type)) {
    return {
      isValid: false,
      error: `File type ${file.type} is not allowed`
    };
  }

  // Validate file size
  if (file.size > maxSize) {
    return {
      isValid: false,
      error: `File size ${file.size} exceeds maximum allowed size of ${maxSize} bytes`
    };
  }

  // Validate file extension
  const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
  if (!allowedExtensions.includes(extension)) {
    return {
      isValid: false,
      error: `File extension ${extension} is not allowed`
    };
  }

  // Sanitize file name
  const sanitizedName = sanitizeFileName(file.name);
  if (!sanitizedName) {
    return {
      isValid: false,
      error: 'Invalid file name'
    };
  }

  return {
    isValid: true,
    sanitizedName
  };
}

/**
 * Rate limiting helper for preventing brute force attacks
 */
export class RateLimiter {
  private attempts: Map<string, { count: number; resetTime: number }> = new Map();

  constructor(
    private maxAttempts: number = 5,
    private windowMs: number = 15 * 60 * 1000 // 15 minutes
  ) {}

  isAllowed(identifier: string): boolean {
    const now = Date.now();
    const record = this.attempts.get(identifier);

    if (!record || now > record.resetTime) {
      // Reset or create new record
      this.attempts.set(identifier, {
        count: 1,
        resetTime: now + this.windowMs
      });
      return true;
    }

    if (record.count >= this.maxAttempts) {
      return false;
    }

    record.count++;
    return true;
  }

  reset(identifier: string): void {
    this.attempts.delete(identifier);
  }
}