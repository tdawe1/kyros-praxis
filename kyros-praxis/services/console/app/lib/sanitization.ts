/**
 * Input sanitization utilities for preventing XSS and other injection attacks
 * 
 * This module provides server-side and client-side sanitization functions
 * to clean user input before processing or storage.
 */

import DOMPurify from 'dompurify';

/**
 * Sanitization levels for different use cases
 */
export type SanitizationLevel = 'strict' | 'basic' | 'rich';

/**
 * Configuration for HTML sanitization
 */
interface SanitizationConfig {
  allowedTags: string[];
  allowedAttributes: string[];
  forbiddenTags: string[];
  forbiddenAttributes: string[];
  allowDataAttributes: boolean;
}

/**
 * Predefined sanitization configurations
 */
const SANITIZATION_CONFIGS: Record<SanitizationLevel, SanitizationConfig> = {
  strict: {
    allowedTags: ['p', 'br', 'strong', 'em', 'span'],
    allowedAttributes: ['class'],
    forbiddenTags: ['script', 'object', 'embed', 'link', 'style', 'iframe', 'form', 'input', 'button'],
    forbiddenAttributes: ['style', 'onclick', 'onload', 'onerror', 'onmouseover', 'onfocus', 'onblur'],
    allowDataAttributes: false,
  },
  basic: {
    allowedTags: ['p', 'br', 'strong', 'em', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a'],
    allowedAttributes: ['class', 'href', 'target', 'title'],
    forbiddenTags: ['script', 'object', 'embed', 'link', 'style', 'iframe', 'form', 'input', 'button'],
    forbiddenAttributes: ['style', 'onclick', 'onload', 'onerror', 'onmouseover', 'onfocus', 'onblur'],
    allowDataAttributes: false,
  },
  rich: {
    allowedTags: [
      'p', 'br', 'strong', 'em', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
      'ul', 'ol', 'li', 'a', 'img', 'blockquote', 'code', 'pre', 'table', 'thead', 
      'tbody', 'tr', 'td', 'th'
    ],
    allowedAttributes: ['class', 'href', 'target', 'title', 'src', 'alt', 'width', 'height'],
    forbiddenTags: ['script', 'object', 'embed', 'link', 'style', 'iframe', 'form', 'input', 'button'],
    forbiddenAttributes: ['style', 'onclick', 'onload', 'onerror', 'onmouseover', 'onfocus', 'onblur'],
    allowDataAttributes: false,
  },
};

/**
 * Sanitizes HTML content using DOMPurify with the specified security level
 * 
 * @param html - Raw HTML content to sanitize
 * @param level - Sanitization level (strict, basic, or rich)
 * @returns Sanitized HTML safe for rendering
 */
export function sanitizeHtml(html: string, level: SanitizationLevel = 'basic'): string {
  if (!html || typeof html !== 'string') {
    return '';
  }

  // Server-side fallback: strip all HTML tags
  if (typeof window === 'undefined') {
    return html.replace(/<[^>]*>/g, '');
  }

  const config = SANITIZATION_CONFIGS[level];
  
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: config.allowedTags,
    ALLOWED_ATTR: config.allowedAttributes,
    FORBID_TAGS: config.forbiddenTags,
    FORBID_ATTR: config.forbiddenAttributes,
    ALLOW_DATA_ATTR: config.allowDataAttributes,
    FORCE_BODY: false,
    RETURN_DOM: false,
    RETURN_DOM_FRAGMENT: false,
    RETURN_DOM_IMPORT: false,
  });
}

/**
 * Sanitizes plain text by escaping HTML entities and dangerous characters
 * 
 * @param text - Plain text to sanitize
 * @returns Escaped text safe for HTML rendering
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
    .replace(/\//g, '&#x2F;')
    .replace(/\\/g, '&#x5C;')
    .replace(/`/g, '&#x60;');
}

/**
 * Sanitizes a URL to prevent XSS via href attributes
 * 
 * @param url - URL to sanitize
 * @returns Sanitized URL or empty string if unsafe
 */
export function sanitizeUrl(url: string): string {
  if (!url || typeof url !== 'string') {
    return '';
  }

  const trimmedUrl = url.trim().toLowerCase();
  
  // Allow relative URLs
  if (trimmedUrl.startsWith('/') || trimmedUrl.startsWith('./') || trimmedUrl.startsWith('../')) {
    return url;
  }
  
  // Allow safe protocols
  const safeProtocols = ['http:', 'https:', 'mailto:', 'tel:', 'ftp:'];
  for (const protocol of safeProtocols) {
    if (trimmedUrl.startsWith(protocol)) {
      return url;
    }
  }
  
  // Block dangerous protocols
  const dangerousProtocols = ['javascript:', 'data:', 'vbscript:', 'file:', 'about:'];
  for (const protocol of dangerousProtocols) {
    if (trimmedUrl.startsWith(protocol)) {
      return '';
    }
  }
  
  // Default: reject unknown protocols
  return '';
}

/**
 * Sanitizes CSS values to prevent CSS injection attacks
 * 
 * @param css - CSS value to sanitize
 * @returns Sanitized CSS value
 */
export function sanitizeCSS(css: string): string {
  if (!css || typeof css !== 'string') {
    return '';
  }

  // Remove potentially dangerous CSS constructs
  return css
    .replace(/javascript:/gi, '')
    .replace(/expression\s*\(/gi, '')
    .replace(/@import/gi, '')
    .replace(/url\s*\(/gi, '')
    .replace(/behavior\s*:/gi, '')
    .replace(/-moz-binding/gi, '')
    .replace(/<!--/g, '')
    .replace(/-->/g, '')
    .trim();
}

/**
 * Sanitizes user input for database storage
 * 
 * @param input - User input to sanitize
 * @param options - Sanitization options
 * @returns Sanitized input
 */
export function sanitizeInput(
  input: string, 
  options: {
    maxLength?: number;
    allowHtml?: boolean;
    htmlLevel?: SanitizationLevel;
    stripWhitespace?: boolean;
  } = {}
): string {
  if (!input || typeof input !== 'string') {
    return '';
  }

  let sanitized = input;

  // Strip or sanitize HTML
  if (options.allowHtml) {
    sanitized = sanitizeHtml(sanitized, options.htmlLevel || 'basic');
  } else {
    sanitized = sanitizeText(sanitized);
  }

  // Strip excess whitespace
  if (options.stripWhitespace !== false) {
    sanitized = sanitized.trim().replace(/\s+/g, ' ');
  }

  // Enforce max length
  if (options.maxLength && sanitized.length > options.maxLength) {
    sanitized = sanitized.substring(0, options.maxLength);
  }

  return sanitized;
}

/**
 * Validates and sanitizes email addresses
 * 
 * @param email - Email address to validate and sanitize
 * @returns Sanitized email or empty string if invalid
 */
export function sanitizeEmail(email: string): string {
  if (!email || typeof email !== 'string') {
    return '';
  }

  const sanitized = email.trim().toLowerCase();
  
  // Basic email regex validation
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  
  if (!emailRegex.test(sanitized)) {
    return '';
  }

  return sanitized;
}

/**
 * Sanitizes phone numbers by removing non-numeric characters except +
 * 
 * @param phone - Phone number to sanitize
 * @returns Sanitized phone number
 */
export function sanitizePhone(phone: string): string {
  if (!phone || typeof phone !== 'string') {
    return '';
  }

  // Remove all characters except digits, +, and common separators
  const cleaned = phone.replace(/[^\d+\-\s\(\)\.]/g, '');
  
  // Basic validation: must start with + or digit
  if (!/^[\+\d]/.test(cleaned)) {
    return '';
  }

  return cleaned.trim();
}

/**
 * Sanitizes file names to prevent path traversal and other attacks
 * 
 * @param filename - File name to sanitize
 * @returns Sanitized file name
 */
export function sanitizeFilename(filename: string): string {
  if (!filename || typeof filename !== 'string') {
    return '';
  }

  return filename
    .replace(/[<>:"/\\|?*]/g, '') // Remove dangerous characters
    .replace(/\.\./g, '') // Remove path traversal
    .replace(/^\.+/, '') // Remove leading dots
    .trim()
    .substring(0, 255); // Limit length
}

/**
 * Validates and sanitizes JSON input
 * 
 * @param jsonString - JSON string to validate and sanitize
 * @returns Parsed and sanitized object or null if invalid
 */
export function sanitizeJSON(jsonString: string): any {
  if (!jsonString || typeof jsonString !== 'string') {
    return null;
  }

  try {
    const parsed = JSON.parse(jsonString);
    
    // Recursively sanitize string values in the object
    return sanitizeObjectStrings(parsed);
  } catch (error) {
    return null;
  }
}

/**
 * Recursively sanitizes string values in an object
 * 
 * @param obj - Object to sanitize
 * @returns Sanitized object
 */
function sanitizeObjectStrings(obj: any): any {
  if (typeof obj === 'string') {
    return sanitizeText(obj);
  }
  
  if (Array.isArray(obj)) {
    return obj.map(sanitizeObjectStrings);
  }
  
  if (obj && typeof obj === 'object') {
    const sanitized: any = {};
    for (const [key, value] of Object.entries(obj)) {
      const sanitizedKey = sanitizeText(key);
      sanitized[sanitizedKey] = sanitizeObjectStrings(value);
    }
    return sanitized;
  }
  
  return obj;
}

/**
 * Content Security Policy (CSP) utilities
 */
export const CSP = {
  /**
   * Generates a random nonce for CSP headers
   * 
   * @returns Random nonce string
   */
  generateNonce(): string {
    if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
      const array = new Uint8Array(16);
      crypto.getRandomValues(array);
      return btoa(String.fromCharCode.apply(null, Array.from(array)));
    }
    
    // Fallback for Node.js environments
    return Math.random().toString(36).substring(2) + Date.now().toString(36);
  },

  /**
   * Creates a CSP header value for the given configuration
   * 
   * @param config - CSP configuration
   * @returns CSP header value
   */
  createHeader(config: {
    defaultSrc?: string[];
    scriptSrc?: string[];
    styleSrc?: string[];
    imgSrc?: string[];
    connectSrc?: string[];
    fontSrc?: string[];
    objectSrc?: string[];
    mediaSrc?: string[];
    frameSrc?: string[];
    nonce?: string;
  }): string {
    const directives: string[] = [];

    if (config.defaultSrc) {
      directives.push(`default-src ${config.defaultSrc.join(' ')}`);
    }

    if (config.scriptSrc) {
      const sources = [...config.scriptSrc];
      if (config.nonce) {
        sources.push(`'nonce-${config.nonce}'`);
      }
      directives.push(`script-src ${sources.join(' ')}`);
    }

    if (config.styleSrc) {
      directives.push(`style-src ${config.styleSrc.join(' ')}`);
    }

    if (config.imgSrc) {
      directives.push(`img-src ${config.imgSrc.join(' ')}`);
    }

    if (config.connectSrc) {
      directives.push(`connect-src ${config.connectSrc.join(' ')}`);
    }

    if (config.fontSrc) {
      directives.push(`font-src ${config.fontSrc.join(' ')}`);
    }

    if (config.objectSrc) {
      directives.push(`object-src ${config.objectSrc.join(' ')}`);
    }

    if (config.mediaSrc) {
      directives.push(`media-src ${config.mediaSrc.join(' ')}`);
    }

    if (config.frameSrc) {
      directives.push(`frame-src ${config.frameSrc.join(' ')}`);
    }

    return directives.join('; ');
  },
};