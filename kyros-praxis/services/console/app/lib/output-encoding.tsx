/**
 * Output encoding utilities for safe dynamic content rendering
 */

import React from 'react';
import { sanitizeHtml, sanitizeText } from './sanitization';

/**
 * Safe HTML renderer component props
 */
export interface SafeHtmlProps {
  html: string;
  level?: 'strict' | 'basic' | 'rich';
  className?: string;
}

/**
 * React component for safely rendering HTML content
 * Use this instead of dangerouslySetInnerHTML
 */
export function SafeHtml({ html, level = 'basic', className }: SafeHtmlProps) {
  const sanitizedHtml = sanitizeHtml(html, level);
  
  return (
    <div 
      className={className}
      dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
    />
  );
}

/**
 * Safe text renderer that escapes HTML entities
 */
export function SafeText({ text, className }: { text: string; className?: string }) {
  const sanitizedText = sanitizeText(text);
  
  return (
    <span className={className}>
      {sanitizedText}
    </span>
  );
}

/**
 * Utility for safe JSON display
 */
export function SafeJsonDisplay({ 
  data, 
  className,
  maxDepth = 3 
}: { 
  data: any; 
  className?: string;
  maxDepth?: number;
}) {
  const safeData = sanitizeJsonForDisplay(data, maxDepth);
  
  return (
    <pre className={className}>
      {JSON.stringify(safeData, null, 2)}
    </pre>
  );
}

/**
 * Recursively sanitize JSON data for safe display
 */
function sanitizeJsonForDisplay(data: any, maxDepth: number, currentDepth = 0): any {
  if (currentDepth >= maxDepth) {
    return '[Max depth reached]';
  }

  if (data === null || data === undefined) {
    return data;
  }

  if (typeof data === 'string') {
    return sanitizeText(data);
  }

  if (typeof data === 'number' || typeof data === 'boolean') {
    return data;
  }

  if (Array.isArray(data)) {
    return data.map(item => 
      sanitizeJsonForDisplay(item, maxDepth, currentDepth + 1)
    );
  }

  if (typeof data === 'object') {
    const sanitized: any = {};
    for (const [key, value] of Object.entries(data)) {
      const sanitizedKey = sanitizeText(key);
      sanitized[sanitizedKey] = sanitizeJsonForDisplay(value, maxDepth, currentDepth + 1);
    }
    return sanitized;
  }

  return '[Unsupported type]';
}

/**
 * Safe attribute value encoding
 */
export function encodeAttribute(value: string): string {
  if (!value || typeof value !== 'string') {
    return '';
  }

  return value
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/**
 * Safe CSS value encoding
 */
export function encodeCssValue(value: string): string {
  if (!value || typeof value !== 'string') {
    return '';
  }

  // Remove potentially dangerous CSS
  return value
    .replace(/expression\s*\(/gi, '') // Remove IE expressions
    .replace(/javascript\s*:/gi, '') // Remove javascript: URLs
    .replace(/vbscript\s*:/gi, '') // Remove vbscript: URLs
    .replace(/data\s*:/gi, '') // Remove data: URLs
    .replace(/behavior\s*:/gi, '') // Remove IE behaviors
    .replace(/[<>"']/g, ''); // Remove HTML chars
}

/**
 * Safe URL encoding for href attributes
 */
export function encodeUrl(url: string): string {
  if (!url || typeof url !== 'string') {
    return '';
  }

  try {
    // Use URL constructor to validate and normalize
    const urlObj = new URL(url, 'https://example.com');
    
    // Only allow safe protocols
    const allowedProtocols = ['http:', 'https:', 'mailto:', 'tel:'];
    if (!allowedProtocols.includes(urlObj.protocol)) {
      return '';
    }

    return urlObj.toString();
  } catch {
    // If URL parsing fails, return empty string
    return '';
  }
}

/**
 * Template literal tag for safe HTML
 * Usage: safeHtml`<p>${userInput}</p>`
 */
export function safeHtml(strings: TemplateStringsArray, ...values: any[]) {
  let result = '';
  
  for (let i = 0; i < strings.length; i++) {
    result += strings[i];
    
    if (i < values.length) {
      const value = values[i];
      result += typeof value === 'string' ? sanitizeText(value) : String(value);
    }
  }
  
  return result;
}

/**
 * React hook for safe dynamic content
 */
export function useSafeContent(content: string, level: 'strict' | 'basic' | 'rich' = 'basic') {
  return {
    sanitizedHtml: sanitizeHtml(content, level),
    sanitizedText: sanitizeText(content)
  };
}

/**
 * Content Security Policy nonce helper
 */
export function useCSPNonce(): string | undefined {
  if (typeof window !== 'undefined') {
    // Get nonce from meta tag (set by middleware)
    const metaTag = document.querySelector('meta[name="csp-nonce"]');
    return metaTag?.getAttribute('content') || undefined;
  }
  return undefined;
}