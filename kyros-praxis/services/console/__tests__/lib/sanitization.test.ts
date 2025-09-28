/**
 * Tests for input sanitization utilities
 */

import {
  sanitizeHtml,
  sanitizeText,
  sanitizeUrl,
  sanitizeJson,
  sanitizeFileName,
  sanitizeEmail,
  sanitizeSearchQuery,
  sanitizeFormData,
  validateFileUpload,
  RateLimiter
} from '../../app/lib/sanitization';

describe('sanitizeHtml', () => {
  test('removes script tags', () => {
    const malicious = '<script>alert("xss")</script><p>Safe content</p>';
    const result = sanitizeHtml(malicious);
    expect(result).toBe('<p>Safe content</p>');
  });

  test('removes dangerous attributes', () => {
    const malicious = '<a href="#" onclick="alert(\'xss\')">Link</a>';
    const result = sanitizeHtml(malicious, 'basic');
    expect(result).toBe('<a href="#">Link</a>');
  });

  test('allows safe HTML with basic config', () => {
    const safe = '<p><strong>Bold</strong> and <em>italic</em> text</p>';
    const result = sanitizeHtml(safe, 'basic');
    expect(result).toBe('<p><strong>Bold</strong> and <em>italic</em> text</p>');
  });

  test('handles empty input', () => {
    expect(sanitizeHtml('')).toBe('');
    expect(sanitizeHtml(null as any)).toBe('');
    expect(sanitizeHtml(undefined as any)).toBe('');
  });
});

describe('sanitizeText', () => {
  test('escapes HTML entities', () => {
    const input = '<script>alert("xss")</script>';
    const result = sanitizeText(input);
    expect(result).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;&#x2F;script&gt;');
  });

  test('escapes special characters', () => {
    const input = '& < > " \' /';
    const result = sanitizeText(input);
    expect(result).toBe('&amp; &lt; &gt; &quot; &#x27; &#x2F;');
  });

  test('handles empty input', () => {
    expect(sanitizeText('')).toBe('');
    expect(sanitizeText(null as any)).toBe('');
  });
});

describe('sanitizeUrl', () => {
  test('allows safe URLs', () => {
    expect(sanitizeUrl('https://example.com')).toBe('https://example.com');
    expect(sanitizeUrl('http://localhost:3000')).toBe('http://localhost:3000');
    expect(sanitizeUrl('mailto:test@example.com')).toBe('mailto:test@example.com');
    expect(sanitizeUrl('/relative/path')).toBe('/relative/path');
  });

  test('blocks dangerous protocols', () => {
    expect(sanitizeUrl('javascript:alert("xss")')).toBe('');
    expect(sanitizeUrl('data:text/html,<script>alert(1)</script>')).toBe('');
    expect(sanitizeUrl('vbscript:msgbox("xss")')).toBe('');
  });

  test('handles empty input', () => {
    expect(sanitizeUrl('')).toBe('');
    expect(sanitizeUrl(null as any)).toBe('');
  });
});

describe('sanitizeJson', () => {
  test('validates and normalizes JSON', () => {
    const input = '{"key": "value", "num": 123}';
    const result = sanitizeJson(input);
    expect(JSON.parse(result)).toEqual({ key: 'value', num: 123 });
  });

  test('handles invalid JSON', () => {
    const invalid = '{key: "value"'; // Missing quote and brace
    const result = sanitizeJson(invalid);
    expect(result).toBe('{}');
  });

  test('handles empty input', () => {
    expect(sanitizeJson('')).toBe('{}');
    expect(sanitizeJson(null as any)).toBe('{}');
  });
});

describe('sanitizeFileName', () => {
  test('removes path traversal attempts', () => {
    expect(sanitizeFileName('../../../etc/passwd')).toBe('etcpasswd');
    expect(sanitizeFileName('..\\..\\windows\\system32')).toBe('windowssystem32');
  });

  test('removes dangerous characters', () => {
    expect(sanitizeFileName('file<>:"|?*.txt')).toBe('file.txt');
  });

  test('handles empty input', () => {
    expect(sanitizeFileName('')).toBe('');
    expect(sanitizeFileName('...')).toBe('');
  });
});

describe('sanitizeEmail', () => {
  test('validates and normalizes email', () => {
    expect(sanitizeEmail('Test@Example.COM')).toBe('test@example.com');
    expect(sanitizeEmail(' user@domain.org ')).toBe('user@domain.org');
  });

  test('rejects invalid emails', () => {
    expect(sanitizeEmail('invalid-email')).toBe('');
    expect(sanitizeEmail('@domain.com')).toBe('');
    expect(sanitizeEmail('user@')).toBe('');
  });

  test('handles empty input', () => {
    expect(sanitizeEmail('')).toBe('');
    expect(sanitizeEmail(null as any)).toBe('');
  });
});

describe('sanitizeSearchQuery', () => {
  test('removes SQL injection patterns', () => {
    expect(sanitizeSearchQuery("' OR 1=1--")).toBe('OR 1=1');
    expect(sanitizeSearchQuery('query; DROP TABLE users;')).toBe('query DROP TABLE users');
  });

  test('removes HTML tags', () => {
    expect(sanitizeSearchQuery('<script>alert("xss")</script>search')).toBe('search');
    expect(sanitizeSearchQuery('<div>content</div>')).toBe('content');
  });

  test('limits length', () => {
    const longQuery = 'a'.repeat(1500);
    const result = sanitizeSearchQuery(longQuery);
    expect(result.length).toBe(1000);
  });
});

describe('sanitizeFormData', () => {
  test('sanitizes string values', () => {
    const input = {
      name: '<script>alert("xss")</script>John',
      description: 'Safe description'
    };
    const result = sanitizeFormData(input);
    expect(result.name).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;&#x2F;script&gt;John');
    expect(result.description).toBe('Safe description');
  });

  test('preserves non-string values', () => {
    const input = {
      id: 123,
      active: true,
      tags: ['tag1', '<script>alert("xss")</script>tag2']
    };
    const result = sanitizeFormData(input);
    expect(result.id).toBe(123);
    expect(result.active).toBe(true);
    expect(result.tags[1]).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;&#x2F;script&gt;tag2');
  });

  test('handles nested objects', () => {
    const input = {
      user: {
        name: '<script>alert("xss")</script>',
        profile: {
          bio: 'Safe bio'
        }
      }
    };
    const result = sanitizeFormData(input);
    expect(result.user.name).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;&#x2F;script&gt;');
    expect(result.user.profile.bio).toBe('Safe bio');
  });
});

describe('validateFileUpload', () => {
  test('validates allowed file types', () => {
    const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' });
    const result = validateFileUpload(file);
    expect(result.isValid).toBe(true);
    expect(result.sanitizedName).toBe('test.jpg');
  });

  test('rejects disallowed file types', () => {
    const file = new File(['content'], 'malicious.exe', { type: 'application/x-executable' });
    const result = validateFileUpload(file);
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('File type');
  });

  test('validates file size', () => {
    const largeFile = new File(['x'.repeat(11 * 1024 * 1024)], 'large.txt', { type: 'text/plain' });
    const result = validateFileUpload(largeFile);
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('File size');
  });

  test('sanitizes file names', () => {
    const file = new File(['content'], '../../../etc/passwd.txt', { type: 'text/plain' });
    const result = validateFileUpload(file);
    expect(result.isValid).toBe(true);
    expect(result.sanitizedName).toBe('etcpasswd.txt');
  });
});

describe('RateLimiter', () => {
  test('allows requests within limit', () => {
    const limiter = new RateLimiter(5, 1000);
    
    for (let i = 0; i < 5; i++) {
      expect(limiter.isAllowed('test-user')).toBe(true);
    }
  });

  test('blocks requests over limit', () => {
    const limiter = new RateLimiter(3, 1000);
    
    // Use up the limit
    for (let i = 0; i < 3; i++) {
      limiter.isAllowed('test-user');
    }
    
    // Should be blocked
    expect(limiter.isAllowed('test-user')).toBe(false);
  });

  test('resets after window expires', (done) => {
    const limiter = new RateLimiter(1, 100); // 100ms window
    
    limiter.isAllowed('test-user');
    expect(limiter.isAllowed('test-user')).toBe(false);
    
    setTimeout(() => {
      expect(limiter.isAllowed('test-user')).toBe(true);
      done();
    }, 150);
  });

  test('can manually reset', () => {
    const limiter = new RateLimiter(1, 1000);
    
    limiter.isAllowed('test-user');
    expect(limiter.isAllowed('test-user')).toBe(false);
    
    limiter.reset('test-user');
    expect(limiter.isAllowed('test-user')).toBe(true);
  });
});