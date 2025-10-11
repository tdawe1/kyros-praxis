/**
 * Output encoding utilities for safe dynamic content rendering
 * 
 * This module provides secure components and utilities for rendering user-provided
 * HTML content while preventing XSS attacks through proper sanitization.
 */

'use client';

import React from 'react';
import DOMPurify from 'dompurify';

/**
 * Safe HTML renderer component props
 */
export interface SafeHtmlProps {
  /** HTML content to be sanitized and rendered */
  html: string;
  /** Sanitization level - controls how strict the sanitization is */
  level?: 'strict' | 'basic' | 'rich';
  /** Additional CSS classes to apply to the container */
  className?: string;
  /** Optional tag name for the container element */
  tag?: keyof JSX.IntrinsicElements;
}

/**
 * Safe text renderer component props
 */
export interface SafeTextProps {
  /** Text content to be safely rendered */
  text: string;
  /** Additional CSS classes to apply to the container */
  className?: string;
  /** Optional tag name for the container element */
  tag?: keyof JSX.IntrinsicElements;
}

/**
 * DOMPurify configuration for different security levels
 */
const getSanitizeConfig = (level: 'strict' | 'basic' | 'rich') => {
  const configs = {
    strict: {
      ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'span'],
      ALLOWED_ATTR: ['class'],
      FORBID_ATTR: ['style', 'onclick', 'onload', 'onerror'],
      FORBID_TAGS: ['script', 'object', 'embed', 'link', 'style', 'iframe'],
    },
    basic: {
      ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a'],
      ALLOWED_ATTR: ['class', 'href', 'target'],
      FORBID_ATTR: ['style', 'onclick', 'onload', 'onerror'],
      FORBID_TAGS: ['script', 'object', 'embed', 'link', 'style', 'iframe'],
      ALLOW_DATA_ATTR: false,
    },
    rich: {
      ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'img', 'blockquote', 'code', 'pre'],
      ALLOWED_ATTR: ['class', 'href', 'target', 'src', 'alt', 'title'],
      FORBID_ATTR: ['style', 'onclick', 'onload', 'onerror', 'javascript:'],
      FORBID_TAGS: ['script', 'object', 'embed', 'link', 'style', 'iframe'],
      ALLOW_DATA_ATTR: false,
    },
  };
  
  return configs[level];
};

/**
 * Sanitizes HTML content using DOMPurify with configurable security levels
 * 
 * @param html - Raw HTML content to sanitize
 * @param level - Security level: 'strict', 'basic', or 'rich'
 * @returns Sanitized HTML string safe for rendering
 */
export const sanitizeHtml = (html: string, level: 'strict' | 'basic' | 'rich' = 'basic'): string => {
  if (!html || typeof html !== 'string') {
    return '';
  }

  // Ensure we're running in the browser
  if (typeof window === 'undefined') {
    // Server-side: strip all HTML tags for safety
    return html.replace(/<[^>]*>/g, '');
  }

  const config = getSanitizeConfig(level);
  return DOMPurify.sanitize(html, config);
};

/**
 * Sanitizes plain text by escaping HTML entities
 * 
 * @param text - Plain text to sanitize
 * @returns Escaped text safe for rendering
 */
export const sanitizeText = (text: string): string => {
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
};

/**
 * React component for safely rendering HTML content
 * 
 * This component uses DOMPurify to sanitize HTML content before rendering,
 * preventing XSS attacks while allowing safe HTML formatting.
 * 
 * @example
 * ```tsx
 * <SafeHtml 
 *   html="<p>Safe <strong>formatted</strong> content</p>" 
 *   level="basic"
 *   className="content"
 * />
 * ```
 */
export function SafeHtml({ 
  html, 
  level = 'basic', 
  className,
  tag: Tag = 'div'
}: SafeHtmlProps) {
  // Always sanitize the HTML content
  const sanitizedHtml = sanitizeHtml(html, level);
  
  // Use dangerouslySetInnerHTML only with sanitized content
  // This is safe because we've sanitized the content with DOMPurify
  return (
    <Tag 
      className={className}
      dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
    />
  );
}

/**
 * React component for safely rendering plain text content
 * 
 * This component renders plain text safely by escaping HTML entities,
 * ensuring no HTML interpretation occurs.
 * 
 * @example
 * ```tsx
 * <SafeText 
 *   text="User input: <script>alert('xss')</script>" 
 *   className="user-content"
 * />
 * ```
 */
export function SafeText({ 
  text, 
  className,
  tag: Tag = 'span'
}: SafeTextProps) {
  // For plain text, we don't need dangerouslySetInnerHTML at all
  // React automatically escapes the content
  return (
    <Tag className={className}>
      {text}
    </Tag>
  );
}

/**
 * Validates if a URL is safe for use in href attributes
 * 
 * @param url - URL to validate
 * @returns True if the URL is safe, false otherwise
 */
export const isSafeUrl = (url: string): boolean => {
  if (!url || typeof url !== 'string') {
    return false;
  }

  // Allow relative URLs and safe protocols
  const safeProtocols = ['http:', 'https:', 'mailto:', 'tel:'];
  const trimmedUrl = url.trim().toLowerCase();
  
  // Relative URLs are generally safe
  if (trimmedUrl.startsWith('/') || trimmedUrl.startsWith('./') || trimmedUrl.startsWith('../')) {
    return true;
  }
  
  // Check for safe protocols
  for (const protocol of safeProtocols) {
    if (trimmedUrl.startsWith(protocol)) {
      return true;
    }
  }
  
  // Block dangerous protocols
  const dangerousProtocols = ['javascript:', 'data:', 'vbscript:', 'file:', 'ftp:'];
  for (const protocol of dangerousProtocols) {
    if (trimmedUrl.startsWith(protocol)) {
      return false;
    }
  }
  
  return false;
};

/**
 * Renders a safe link component with URL validation
 * 
 * @param href - URL for the link
 * @param children - Link content
 * @param className - CSS classes
 * @param target - Link target
 */
export function SafeLink({ 
  href, 
  children, 
  className,
  target,
  ...props 
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
  target?: string;
} & React.AnchorHTMLAttributes<HTMLAnchorElement>) {
  // Only render link if URL is safe
  if (!isSafeUrl(href)) {
    return <span className={className}>{children}</span>;
  }

  return (
    <a 
      href={href} 
      className={className}
      target={target}
      rel={target === '_blank' ? 'noopener noreferrer' : undefined}
      {...props}
    >
      {children}
    </a>
  );
}