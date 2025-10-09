# Security Implementation: XSS Prevention Guide

## Overview

This document explains the security measures implemented to fix the `dangerouslySetInnerHTML` vulnerability identified in the security audit. The solution provides comprehensive XSS protection while maintaining functionality for legitimate HTML content.

## The Problem

The original security issue was:
- Use of `dangerouslySetInnerHTML` with non-constant definitions
- Potential for XSS attacks if user-provided input contains malicious HTML
- Risk of client-side code execution, session hijacking, and data theft

## The Solution

We implemented a comprehensive security layer using **DOMPurify** as recommended:

### 1. SafeHtml Component

Replaces unsafe `dangerouslySetInnerHTML` usage:

```tsx
// ❌ VULNERABLE - DO NOT USE
<div dangerouslySetInnerHTML={{ __html: userContent }} />

// ✅ SECURE - USE THIS INSTEAD
<SafeHtml html={userContent} level="basic" />
```

### 2. Security Levels

Three configurable security levels:

- **strict**: Only basic text formatting (`p`, `br`, `strong`, `em`, `span`)
- **basic**: Common formatting + links (`h1-h6`, `ul`, `ol`, `li`, `a`)
- **rich**: Advanced formatting + images (`img`, `blockquote`, `code`, `table`)

### 3. Component Usage Examples

```tsx
import { SafeHtml, SafeText, SafeLink } from '@/lib/output-encoding';

// Safe HTML with different security levels
<SafeHtml html={userContent} level="strict" />   // Most secure
<SafeHtml html={userContent} level="basic" />    // Balanced
<SafeHtml html={userContent} level="rich" />     // Feature-rich

// Safe plain text (no HTML interpretation)
<SafeText text={userInput} />

// Safe links with URL validation
<SafeLink href={userProvidedUrl}>Click here</SafeLink>
```

## Security Features Implemented

### 1. HTML Sanitization

- **Script Removal**: All `<script>` tags are completely removed
- **Event Handler Blocking**: Removes `onclick`, `onerror`, `onload`, etc.
- **Dangerous Tag Filtering**: Blocks `<iframe>`, `<object>`, `<embed>`, `<form>`
- **Attribute Filtering**: Only allows safe attributes like `class`, `href`, `src`

### 2. URL Validation

```tsx
// Blocked URLs (returns empty span):
javascript:alert('xss')
data:text/html,<script>alert('xss')</script>
vbscript:msgbox('xss')

// Allowed URLs:
https://example.com
/internal/path
./relative/path
mailto:user@example.com
```

### 3. Server-Side Safety

- When `window` is undefined (SSR), HTML tags are stripped entirely
- Prevents any potential server-side vulnerabilities

### 4. Input Sanitization Utilities

```tsx
import { 
  sanitizeHtml, 
  sanitizeText, 
  sanitizeUrl,
  sanitizeInput 
} from '@/lib/sanitization';

// Individual sanitization functions
const safeHtml = sanitizeHtml(userHtml, 'basic');
const safeText = sanitizeText(userText);
const safeUrl = sanitizeUrl(userUrl);

// Comprehensive input sanitization
const safeInput = sanitizeInput(userInput, {
  maxLength: 1000,
  allowHtml: true,
  htmlLevel: 'basic',
  stripWhitespace: true
});
```

## Migration Guide

### Before (Vulnerable)

```tsx
function UserContent({ html }) {
  return (
    <div dangerouslySetInnerHTML={{ __html: html }} />
  );
}
```

### After (Secure)

```tsx
import { SafeHtml } from '@/lib/output-encoding';

function UserContent({ html }) {
  return (
    <SafeHtml 
      html={html} 
      level="basic"
      className="user-content"
    />
  );
}
```

### For Plain Text

```tsx
import { SafeText } from '@/lib/output-encoding';

function UserComment({ text }) {
  return (
    <SafeText 
      text={text}
      className="comment-text"
    />
  );
}
```

### For User Links

```tsx
import { SafeLink } from '@/lib/output-encoding';

function UserLink({ href, children }) {
  return (
    <SafeLink 
      href={href}
      target="_blank"
      className="user-link"
    >
      {children}
    </SafeLink>
  );
}
```

## Testing Strategy

Our implementation includes comprehensive tests that verify:

1. **Script Injection Prevention**
2. **Event Handler Removal**
3. **Dangerous URL Blocking**
4. **Server-Side Safety**
5. **Configuration Levels**

Run tests with:
```bash
npm test -- app/lib/__tests__/output-encoding.test.tsx
```

## Content Security Policy (CSP)

The implementation works with our existing CSP headers:

```
Content-Security-Policy: 
  default-src 'self';
  script-src 'self';
  style-src 'self';
  object-src 'none';
```

## Performance Considerations

- **Client-Side**: DOMPurify is lightweight (~45KB) and very fast
- **Server-Side**: Falls back to simple regex HTML stripping
- **Caching**: Sanitized content can be cached safely
- **Bundle Size**: Only loads DOMPurify in browser environment

## Best Practices

### 1. Always Use Security Components

```tsx
// ✅ DO
<SafeHtml html={userContent} level="basic" />

// ❌ DON'T
<div dangerouslySetInnerHTML={{ __html: userContent }} />
```

### 2. Choose Appropriate Security Level

```tsx
// User comments - use strict
<SafeHtml html={comment} level="strict" />

// Blog posts - use basic  
<SafeHtml html={blogPost} level="basic" />

// Rich content editors - use rich
<SafeHtml html={editorContent} level="rich" />
```

### 3. Validate URLs

```tsx
// Always use SafeLink for user-provided URLs
<SafeLink href={userUrl}>Link Text</SafeLink>
```

### 4. Handle Edge Cases

```tsx
// Check for empty/null content
<SafeHtml 
  html={content || ''} 
  level="basic" 
/>

// Provide fallback for invalid URLs
<SafeLink href={url}>
  {url ? 'Visit Link' : 'Invalid URL'}
</SafeLink>
```

## Security Audit Compliance

✅ **Fixed**: dangerouslySetInnerHTML with non-constant definition  
✅ **Implemented**: DOMPurify sanitization as recommended  
✅ **Added**: Comprehensive input validation  
✅ **Tested**: XSS prevention with automated tests  
✅ **Documented**: Usage guidelines and migration path  

## Monitoring and Maintenance

1. **Regular Updates**: Keep DOMPurify updated for latest security patches
2. **CSP Monitoring**: Monitor CSP violation reports
3. **Security Audits**: Regular security testing of user input handling
4. **Performance Monitoring**: Track sanitization performance impact

## Summary

This implementation completely eliminates the XSS vulnerability by:

1. **Sanitizing all HTML** before using `dangerouslySetInnerHTML`
2. **Validating URLs** to prevent protocol-based attacks
3. **Providing safe alternatives** for common use cases
4. **Maintaining functionality** while ensuring security
5. **Including comprehensive tests** to prevent regressions

The solution follows security best practices and provides a sustainable, maintainable approach to handling user-generated content safely.