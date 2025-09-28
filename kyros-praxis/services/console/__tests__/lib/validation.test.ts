/**
 * Tests for input validation utilities
 */

import {
  sanitizedString,
  sanitizedUrl,
  sanitizedEmail,
  sanitizedSearchQuery,
  SuperConsoleFormSchema,
  AuthFormSchema,
  SearchFormSchema,
  FileUploadSchema,
  UrlParamsSchema,
  validateInput,
  validateUrlParams,
  generateCSRFToken,
  validateCSRFToken,
  validateContentType,
  validateRequestSize,
  ValidationPatterns
} from '../../app/lib/validation';

describe('Sanitized Zod transformers', () => {
  describe('sanitizedString', () => {
    test('sanitizes HTML entities', () => {
      const schema = sanitizedString();
      const result = schema.parse('<script>alert("xss")</script>');
      expect(result).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;&#x2F;script&gt;');
    });

    test('enforces length limits', () => {
      const schema = sanitizedString(10);
      expect(() => schema.parse('a'.repeat(15))).toThrow();
    });
  });

  describe('sanitizedUrl', () => {
    test('allows safe URLs', () => {
      const schema = sanitizedUrl();
      expect(schema.parse('https://example.com')).toBe('https://example.com');
    });

    test('blocks dangerous URLs', () => {
      const schema = sanitizedUrl();
      expect(() => schema.parse('javascript:alert("xss")')).toThrow();
    });
  });

  describe('sanitizedEmail', () => {
    test('normalizes valid emails', () => {
      const schema = sanitizedEmail();
      expect(schema.parse('Test@Example.COM')).toBe('test@example.com');
    });

    test('rejects invalid emails', () => {
      const schema = sanitizedEmail();
      expect(() => schema.parse('invalid-email')).toThrow();
    });
  });
});

describe('Form schemas', () => {
  describe('SuperConsoleFormSchema', () => {
    test('validates valid super console data', () => {
      const data = {
        target: 'api-server',
        mode: 'send',
        packet: '{"message": "hello"}'
      };
      const result = SuperConsoleFormSchema.parse(data);
      expect(result.target).toBe('api-server');
      expect(result.mode).toBe('send');
      expect(result.packet).toBe('{"message":"hello"}');
    });

    test('sanitizes malicious input', () => {
      const data = {
        target: '<script>alert("xss")</script>target',
        mode: 'send<script>',
        packet: '{"message": "safe"}'
      };
      const result = SuperConsoleFormSchema.parse(data);
      expect(result.target).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;&#x2F;script&gt;target');
      expect(result.mode).toBe('send&lt;script&gt;');
    });

    test('handles invalid JSON gracefully', () => {
      const data = {
        target: 'target',
        mode: 'send',
        packet: '{invalid json'
      };
      const result = SuperConsoleFormSchema.parse(data);
      expect(result.packet).toBe('{}');
    });

    test('rejects missing required fields', () => {
      const data = {
        target: '',
        mode: 'send',
        packet: '{}'
      };
      expect(() => SuperConsoleFormSchema.parse(data)).toThrow();
    });
  });

  describe('AuthFormSchema', () => {
    test('validates valid auth data', () => {
      const data = {
        email: 'user@example.com',
        password: 'strongpassword123'
      };
      const result = AuthFormSchema.parse(data);
      expect(result.email).toBe('user@example.com');
      expect(result.password).toBe('strongpassword123');
    });

    test('rejects weak passwords', () => {
      const data = {
        email: 'user@example.com',
        password: 'weak'
      };
      expect(() => AuthFormSchema.parse(data)).toThrow();
    });

    test('rejects invalid emails', () => {
      const data = {
        email: 'invalid-email',
        password: 'strongpassword123'
      };
      expect(() => AuthFormSchema.parse(data)).toThrow();
    });
  });

  describe('SearchFormSchema', () => {
    test('validates search data', () => {
      const data = {
        query: 'test search',
        limit: 25,
        offset: 50
      };
      const result = SearchFormSchema.parse(data);
      expect(result.query).toBe('test search');
      expect(result.limit).toBe(25);
      expect(result.offset).toBe(50);
    });

    test('applies defaults', () => {
      const result = SearchFormSchema.parse({});
      expect(result.limit).toBe(50);
      expect(result.offset).toBe(0);
    });

    test('sanitizes query', () => {
      const data = {
        query: "'; DROP TABLE users; --"
      };
      const result = SearchFormSchema.parse(data);
      expect(result.query).toBe('DROP TABLE users');
    });
  });

  describe('FileUploadSchema', () => {
    test('validates file upload data', () => {
      const data = {
        fileName: 'document.pdf',
        fileType: 'application/pdf',
        fileSize: 1024 * 1024 // 1MB
      };
      const result = FileUploadSchema.parse(data);
      expect(result.fileName).toBe('document.pdf');
      expect(result.fileType).toBe('application/pdf');
      expect(result.fileSize).toBe(1024 * 1024);
    });

    test('sanitizes file names', () => {
      const data = {
        fileName: '../../../etc/passwd.txt',
        fileType: 'text/plain',
        fileSize: 100
      };
      const result = FileUploadSchema.parse(data);
      expect(result.fileName).toBe('etcpasswd.txt');
    });

    test('rejects disallowed file types', () => {
      const data = {
        fileName: 'malicious.exe',
        fileType: 'application/x-executable',
        fileSize: 100
      };
      expect(() => FileUploadSchema.parse(data)).toThrow();
    });

    test('rejects oversized files', () => {
      const data = {
        fileName: 'large.pdf',
        fileType: 'application/pdf',
        fileSize: 15 * 1024 * 1024 // 15MB
      };
      expect(() => FileUploadSchema.parse(data)).toThrow();
    });
  });

  describe('UrlParamsSchema', () => {
    test('validates URL parameters', () => {
      const data = {
        page: '2',
        limit: '25',
        search: 'test query',
        sort: 'created_at',
        order: 'desc'
      };
      const result = UrlParamsSchema.parse(data);
      expect(result.page).toBe(2);
      expect(result.limit).toBe(25);
      expect(result.search).toBe('test query');
      expect(result.sort).toBe('created_at');
      expect(result.order).toBe('desc');
    });

    test('handles invalid numeric values', () => {
      const data = {
        page: 'invalid',
        limit: '-5'
      };
      const result = UrlParamsSchema.parse(data);
      expect(result.page).toBe(1);
      expect(result.limit).toBe(50);
    });

    test('restricts sort values', () => {
      const data = {
        sort: 'malicious_field'
      };
      const result = UrlParamsSchema.parse(data);
      expect(result.sort).toBe('created_at');
    });
  });
});

describe('Validation helpers', () => {
  describe('validateInput', () => {
    test('returns success for valid data', () => {
      const schema = sanitizedString();
      const result = validateInput(schema, 'valid input');
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toBe('valid input');
      }
    });

    test('returns errors for invalid data', () => {
      const schema = sanitizedString(5);
      const result = validateInput(schema, 'too long input');
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.errors).toContain(': String must be 5 characters or less');
      }
    });
  });

  describe('validateUrlParams', () => {
    test('validates URL search params', () => {
      const params = new URLSearchParams('page=2&limit=25&search=test');
      const result = validateUrlParams(params);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.page).toBe(2);
      }
    });

    test('sanitizes malicious params', () => {
      const params = new URLSearchParams('search=<script>alert("xss")</script>');
      const result = validateUrlParams(params);
      expect(result.success).toBe(true);
      if (result.success) {
        // Check that the script tags are properly escaped
        expect(result.data.search).toMatch(/&ltscript&gt/);
        expect(result.data.search).not.toContain('<script>');
      }
    });
  });

  describe('CSRF token functions', () => {
    test('generates valid tokens', () => {
      const token = generateCSRFToken();
      expect(token).toHaveLength(64); // 32 bytes * 2 hex chars
    });

    test('validates matching tokens', () => {
      const token = generateCSRFToken();
      expect(validateCSRFToken(token, token)).toBe(true);
    });

    test('rejects non-matching tokens', () => {
      const token1 = generateCSRFToken();
      const token2 = generateCSRFToken();
      expect(validateCSRFToken(token1, token2)).toBe(false);
    });

    test('rejects empty tokens', () => {
      expect(validateCSRFToken('', 'token')).toBe(false);
      expect(validateCSRFToken('token', '')).toBe(false);
    });
  });

  describe('Content type validation', () => {
    test('validates allowed content types', () => {
      const request = new Request('http://test.com', {
        headers: { 'content-type': 'application/json' }
      });
      expect(validateContentType(request, ['application/json'])).toBe(true);
    });

    test('rejects disallowed content types', () => {
      const request = new Request('http://test.com', {
        headers: { 'content-type': 'text/plain' }
      });
      expect(validateContentType(request, ['application/json'])).toBe(false);
    });

    test('handles missing content type', () => {
      const request = new Request('http://test.com');
      expect(validateContentType(request, ['application/json'])).toBe(false);
    });
  });

  describe('Request size validation', () => {
    test('validates request size within limit', () => {
      const request = new Request('http://test.com', {
        headers: { 'content-length': '500' }
      });
      expect(validateRequestSize(request, 1000)).toBe(true);
    });

    test('rejects oversized requests', () => {
      const request = new Request('http://test.com', {
        headers: { 'content-length': '2000' }
      });
      expect(validateRequestSize(request, 1000)).toBe(false);
    });

    test('handles missing content length', () => {
      const request = new Request('http://test.com');
      expect(validateRequestSize(request, 1000)).toBe(false);
    });
  });
});

describe('Validation patterns', () => {
  test('UUID pattern', () => {
    expect(ValidationPatterns.uuid.test('123e4567-e89b-12d3-a456-426614174000')).toBe(true);
    expect(ValidationPatterns.uuid.test('invalid-uuid')).toBe(false);
  });

  test('Safe ID pattern', () => {
    expect(ValidationPatterns.safeId.test('safe_id-123')).toBe(true);
    expect(ValidationPatterns.safeId.test('unsafe@id')).toBe(false);
  });

  test('URL pattern', () => {
    expect(ValidationPatterns.url.test('https://example.com')).toBe(true);
    expect(ValidationPatterns.url.test('invalid-url')).toBe(false);
  });

  test('Email pattern', () => {
    expect(ValidationPatterns.email.test('user@example.com')).toBe(true);
    expect(ValidationPatterns.email.test('invalid-email')).toBe(false);
  });

  test('IPv4 pattern', () => {
    expect(ValidationPatterns.ipv4.test('192.168.1.1')).toBe(true);
    expect(ValidationPatterns.ipv4.test('invalid-ip')).toBe(false);
  });

  test('Safe filename pattern', () => {
    expect(ValidationPatterns.safeFilename.test('document.pdf')).toBe(true);
    expect(ValidationPatterns.safeFilename.test('../malicious')).toBe(false);
  });
});