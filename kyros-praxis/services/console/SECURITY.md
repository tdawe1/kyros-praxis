# Console Service Security Features

This document outlines the comprehensive input sanitization and security measures implemented in the Console service.

## 🔒 Security Features

### Input Sanitization

The Console service implements multi-layered input sanitization to prevent XSS and injection attacks:

#### 1. HTML Sanitization (`sanitizeHtml`)
- Uses DOMPurify for robust HTML cleaning
- Three security levels:
  - **Strict**: Only basic text formatting (`<b>`, `<i>`, `<em>`, `<strong>`, `<u>`)
  - **Basic**: Common formatting + links (`<a>`, `<p>`, `<br>`, lists)
  - **Rich**: Extended HTML for rich text editors (headers, tables, code blocks)
- Removes all dangerous tags (`<script>`, `<iframe>`, `<object>`, etc.)
- Strips malicious attributes (`onclick`, `onerror`, etc.)

#### 2. Text Escaping (`sanitizeText`)
- Escapes HTML entities: `< > & " ' /`
- Prevents XSS through text injection
- Safe for display in HTML contexts

#### 3. URL Validation (`sanitizeUrl`)
- Blocks dangerous protocols: `javascript:`, `data:`, `vbscript:`, etc.
- Only allows: `http:`, `https:`, `mailto:`, `tel:`, and relative URLs
- Prevents XSS through URL injection

#### 4. JSON Sanitization (`sanitizeJson`)
- Validates JSON structure
- Prevents code injection through malformed JSON
- Returns safe empty object `{}` for invalid input

### Form Validation

All forms use Zod schemas with built-in sanitization:

```typescript
// Example: Super Console Form
const formData = { target, mode, packet };
const validation = SuperConsoleFormSchema.safeParse(formData);
if (!validation.success) {
  // Handle validation errors
}
// Use validation.data (sanitized and validated)
```

### API Security

#### Middleware Protection
- **Rate Limiting**: 1000 requests per 15 minutes per IP
- **Content-Type Validation**: Ensures JSON for API endpoints
- **Request Size Limits**: 50MB for uploads, 1MB for regular requests
- **URL Parameter Sanitization**: Automatically cleans query parameters
- **Dangerous Path Blocking**: Blocks common attack paths (`/.env`, `/admin`, etc.)

#### API Route Validation
All API routes use input validation:

```typescript
// Validate and sanitize input using schema
const validation = SuperConsoleFormSchema.safeParse(body);
if (!validation.success) {
  return NextResponse.json({ 
    error: `Input validation failed: ${errorMessages}` 
  }, { status: 400 });
}
```

### File Upload Security

#### File Validation (`validateFileUpload`)
- **Type Restrictions**: Only allows specific MIME types
- **Size Limits**: Configurable max file size (default 10MB)
- **Extension Validation**: Checks file extensions
- **Name Sanitization**: Removes path traversal attempts (`../`)
- **Dangerous Character Removal**: Strips `< > : " | ? *`

#### Usage Example
```typescript
const validation = validateFileUpload(file, {
  allowedTypes: ['image/jpeg', 'image/png', 'application/pdf'],
  maxSize: 5 * 1024 * 1024, // 5MB
  allowedExtensions: ['.jpg', '.png', '.pdf']
});

if (!validation.isValid) {
  console.error(validation.error);
}
```

### Output Encoding

Safe rendering components prevent XSS in dynamic content:

#### SafeHtml Component
```typescript
import { SafeHtml } from '@/lib/output-encoding';

// Safely render HTML content
<SafeHtml 
  html={userGeneratedHtml} 
  level="basic" 
  className="content" 
/>
```

#### SafeText Component
```typescript
import { SafeText } from '@/lib/output-encoding';

// Safely display text with HTML escaping
<SafeText text={userInput} className="user-content" />
```

## 🛡️ Security Headers

The application includes comprehensive security headers via Next.js configuration:

- **Content Security Policy (CSP)**: Restricts resource loading
- **X-XSS-Protection**: Browser XSS filtering
- **X-Content-Type-Options**: Prevents MIME sniffing
- **X-Frame-Options**: Prevents clickjacking
- **Strict-Transport-Security**: Enforces HTTPS
- **Referrer-Policy**: Controls referrer information

## 🧪 Testing

Comprehensive test suite with 76 security tests:

```bash
# Run security tests
npm test -- __tests__/lib/

# Test specific sanitization functions
npm test -- __tests__/lib/sanitization.test.ts

# Test validation utilities
npm test -- __tests__/lib/validation.test.ts
```

## 📋 Security Checklist

- [x] **Input Sanitization**: All user inputs sanitized before processing
- [x] **XSS Prevention**: HTML entities escaped, dangerous tags removed
- [x] **SQL Injection Prevention**: Query parameters sanitized
- [x] **File Upload Security**: Type/size validation, name sanitization
- [x] **URL Security**: Protocol validation, dangerous URLs blocked
- [x] **Rate Limiting**: IP-based request throttling
- [x] **Content Security Policy**: Restrictive CSP headers configured
- [x] **Output Encoding**: Safe rendering components for dynamic content
- [x] **API Validation**: All endpoints validate input data
- [x] **Middleware Protection**: Request filtering and sanitization

## 🔧 Usage Guidelines

### For Developers

1. **Always validate input**: Use provided schemas for all form inputs
2. **Sanitize before storage**: Clean data before database operations
3. **Encode output**: Use SafeHtml/SafeText components for display
4. **Validate file uploads**: Check type, size, and sanitize names
5. **Use provided utilities**: Don't create custom sanitization functions

### Best Practices

1. **Principle of Least Privilege**: Only allow necessary HTML tags/attributes
2. **Defense in Depth**: Multiple layers of validation and sanitization
3. **Input Validation**: Validate on both client and server side
4. **Output Encoding**: Always encode data before rendering
5. **Regular Updates**: Keep DOMPurify and security dependencies updated

## 🚨 Security Incidents

If you discover a security vulnerability:

1. **Do not** create a public issue
2. **Do not** commit fixes to public repositories
3. **Contact** the security team immediately
4. **Follow** responsible disclosure practices

## 📚 References

- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [DOMPurify Documentation](https://github.com/cure53/DOMPurify)
- [Next.js Security Best Practices](https://nextjs.org/docs/app/building-your-application/configuring/content-security-policy)
- [Zod Validation Library](https://zod.dev/)