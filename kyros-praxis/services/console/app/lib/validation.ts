/**
 * Enhanced input validation utilities for security
 */

import { z } from 'zod';
import { sanitizeText, sanitizeUrl, sanitizeEmail, sanitizeSearchQuery } from './sanitization';

/**
 * Custom Zod transformers for automatic sanitization
 */
export const sanitizedString = (maxLength = 1000) =>
  z.string()
    .transform(sanitizeText)
    .refine(val => val.length <= maxLength, {
      message: `String must be ${maxLength} characters or less`
    });

export const sanitizedUrl = () =>
  z.string()
    .transform(sanitizeUrl)
    .refine(val => val.length > 0, {
      message: 'Invalid URL format or dangerous protocol'
    });

export const sanitizedEmail = () =>
  z.string()
    .transform(sanitizeEmail)
    .refine(val => val.length > 0, {
      message: 'Invalid email format'
    });

export const sanitizedSearchQuery = () =>
  z.string()
    .transform(sanitizeSearchQuery)
    .refine(val => val.length > 0, {
      message: 'Search query cannot be empty after sanitization'
    });

/**
 * Enhanced schemas with built-in sanitization
 */

// Super Console Form Schema
export const SuperConsoleFormSchema = z.object({
  target: sanitizedString(100).refine(val => val.length > 0, {
    message: 'Target is required'
  }),
  mode: sanitizedString(50).refine(val => val.length > 0, {
    message: 'Mode is required'
  }),
  packet: z.string()
    .transform(val => {
      try {
        // Validate JSON structure and re-stringify for safety
        const parsed = JSON.parse(val);
        return JSON.stringify(parsed);
      } catch {
        return '{}';
      }
    })
});

// Authentication Form Schema
export const AuthFormSchema = z.object({
  email: sanitizedEmail().refine(val => val.length > 0, {
    message: 'Valid email is required'
  }),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .max(128, 'Password must be less than 128 characters')
    // Don't sanitize passwords as it may break legitimate special characters
});

// Search Form Schema
export const SearchFormSchema = z.object({
  query: sanitizedSearchQuery().optional(),
  filters: z.record(sanitizedString(100)).optional(),
  limit: z.number().int().min(1).max(1000).default(50),
  offset: z.number().int().min(0).default(0)
});

// File Upload Schema
export const FileUploadSchema = z.object({
  fileName: z.string()
    .transform(val => {
      // Basic sanitization for file names
      return val
        .replace(/\.\./g, '')
        .replace(/[\/\\]/g, '')
        .replace(/[\x00-\x1f\x80-\x9f]/g, '')
        .replace(/[<>:"|?*]/g, '')
        .trim()
        .substring(0, 255);
    })
    .refine(val => val.length > 0, {
      message: 'Valid file name is required'
    }),
  fileType: z.string()
    .refine(val => {
      const allowedTypes = [
        'image/jpeg', 'image/png', 'image/gif', 
        'text/plain', 'application/pdf', 'application/json'
      ];
      return allowedTypes.includes(val);
    }, {
      message: 'File type not allowed'
    }),
  fileSize: z.number()
    .max(10 * 1024 * 1024, 'File size must be less than 10MB')
});

// URL Parameter Validation Schema
export const UrlParamsSchema = z.object({
  page: z.string().optional().transform(val => {
    if (!val) return undefined;
    const num = parseInt(val, 10);
    return isNaN(num) || num < 1 ? 1 : Math.min(num, 1000);
  }),
  limit: z.string().optional().transform(val => {
    if (!val) return undefined;
    const num = parseInt(val, 10);
    return isNaN(num) || num < 1 ? 50 : Math.min(num, 100);
  }),
  search: sanitizedSearchQuery().optional(),
  sort: z.string().optional().transform(val => {
    if (!val) return undefined;
    // Only allow specific sort values
    const allowedSorts = ['created_at', 'updated_at', 'name', 'status'];
    return allowedSorts.includes(val) ? val : 'created_at';
  }),
  order: z.string().optional().transform(val => {
    if (!val) return undefined;
    return val.toLowerCase() === 'desc' ? 'desc' : 'asc';
  })
});

/**
 * Input validation middleware helper
 */
export function validateInput<T extends z.ZodType>(
  schema: T,
  data: unknown
): { success: true; data: z.infer<T> } | { success: false; errors: string[] } {
  try {
    const result = schema.parse(data);
    return { success: true, data: result };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errors = error.errors.map(err => 
        `${err.path.join('.')}: ${err.message}`
      );
      return { success: false, errors };
    }
    return { success: false, errors: ['Validation failed'] };
  }
}

/**
 * Validate and sanitize request body
 */
export async function validateRequestBody<T extends z.ZodType>(
  request: Request,
  schema: T
): Promise<{ success: true; data: z.infer<T> } | { success: false; errors: string[] }> {
  try {
    const body = await request.json();
    return validateInput(schema, body);
  } catch {
    return { success: false, errors: ['Invalid JSON in request body'] };
  }
}

/**
 * Validate URL parameters
 */
export function validateUrlParams(
  searchParams: URLSearchParams
): { success: true; data: any } | { success: false; errors: string[] } {
  const params: Record<string, string> = {};
  
  for (const [key, value] of searchParams.entries()) {
    // Sanitize parameter keys and values
    const sanitizedKey = sanitizeText(key);
    const sanitizedValue = sanitizeText(value);
    
    if (sanitizedKey && sanitizedValue) {
      params[sanitizedKey] = sanitizedValue;
    }
  }

  return validateInput(UrlParamsSchema, params);
}

/**
 * CSRF Token validation
 */
export function generateCSRFToken(): string {
  // Generate a cryptographically secure random token
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

export function validateCSRFToken(provided: string, expected: string): boolean {
  if (!provided || !expected || provided.length !== expected.length) {
    return false;
  }

  // Use timing-safe comparison
  let result = 0;
  for (let i = 0; i < provided.length; i++) {
    result |= provided.charCodeAt(i) ^ expected.charCodeAt(i);
  }
  
  return result === 0;
}

/**
 * Content-Type validation for API endpoints
 */
export function validateContentType(request: Request, allowedTypes: string[]): boolean {
  const contentType = request.headers.get('content-type');
  if (!contentType) return false;

  return allowedTypes.some(type => contentType.includes(type));
}

/**
 * Request size validation
 */
export function validateRequestSize(request: Request, maxSize: number = 1024 * 1024): boolean {
  const contentLength = request.headers.get('content-length');
  if (!contentLength) return false;

  const size = parseInt(contentLength, 10);
  return !isNaN(size) && size <= maxSize;
}

/**
 * Common validation patterns
 */
export const ValidationPatterns = {
  // UUID validation
  uuid: /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
  
  // Safe identifier (alphanumeric, underscore, hyphen)
  safeId: /^[a-zA-Z0-9_-]+$/,
  
  // Basic URL validation
  url: /^https?:\/\/[^\s/$.?#].[^\s]*$/,
  
  // Email validation (basic)
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  
  // IPv4 address
  ipv4: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  
  // Safe filename (no path traversal)
  safeFilename: /^[a-zA-Z0-9._-]+$/
};

/**
 * Input sanitization decorator for API routes
 */
export function withInputValidation<T extends z.ZodType>(schema: T) {
  return function(handler: (data: z.infer<T>, request: Request) => Promise<Response>) {
    return async function(request: Request): Promise<Response> {
      // Validate content type
      if (!validateContentType(request, ['application/json'])) {
        return new Response(
          JSON.stringify({ error: 'Content-Type must be application/json' }),
          { status: 400, headers: { 'Content-Type': 'application/json' } }
        );
      }

      // Validate request size
      if (!validateRequestSize(request)) {
        return new Response(
          JSON.stringify({ error: 'Request too large' }),
          { status: 413, headers: { 'Content-Type': 'application/json' } }
        );
      }

      // Validate and sanitize input
      const validation = await validateRequestBody(request, schema);
      if (!validation.success) {
        return new Response(
          JSON.stringify({ error: 'Validation failed', details: validation.errors }),
          { status: 400, headers: { 'Content-Type': 'application/json' } }
        );
      }

      return handler(validation.data, request);
    };
  };
}