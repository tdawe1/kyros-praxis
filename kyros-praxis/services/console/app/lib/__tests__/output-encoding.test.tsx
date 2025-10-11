/**
 * Tests for output encoding utilities
 * Validates XSS prevention and security measures
 */

import '@testing-library/jest-dom';
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import { render, screen } from '@testing-library/react';
import { 
  SafeHtml, 
  SafeText, 
  SafeLink,
  sanitizeHtml, 
  sanitizeText, 
  isSafeUrl 
} from '../output-encoding';

// Mock DOMPurify for server-side testing
const mockDOMPurify = {
  sanitize: jest.fn((html: string) => html),
};

// Mock window for SSR testing
const originalWindow = global.window;

describe('sanitizeHtml', () => {
  beforeEach(() => {
    // Mock browser environment
    Object.defineProperty(global, 'window', {
      value: {},
      writable: true,
    });
    
    // Mock DOMPurify
    jest.doMock('dompurify', () => mockDOMPurify);
  });

  afterEach(() => {
    global.window = originalWindow;
    jest.resetAllMocks();
  });

  it('should return empty string for null/undefined input', () => {
    expect(sanitizeHtml('')).toBe('');
    expect(sanitizeHtml(null as any)).toBe('');
    expect(sanitizeHtml(undefined as any)).toBe('');
  });

  it('should strip HTML tags in server environment', () => {
    // Mock server environment
    delete (global as any).window;
    
    const htmlContent = '<script>alert("xss")</script><p>Safe content</p>';
    const result = sanitizeHtml(htmlContent);
    
    expect(result).toBe('alert("xss")Safe content');
  });

  it('should call DOMPurify.sanitize in browser environment', () => {
    const htmlContent = '<p>Safe content</p>';
    sanitizeHtml(htmlContent, 'basic');
    
    expect(mockDOMPurify.sanitize).toHaveBeenCalledWith(
      htmlContent,
      expect.objectContaining({
        ALLOWED_TAGS: expect.arrayContaining(['p', 'br', 'strong']),
        FORBID_TAGS: expect.arrayContaining(['script', 'object', 'embed']),
      })
    );
  });

  it('should use strict config for strict level', () => {
    const htmlContent = '<p>Content</p>';
    sanitizeHtml(htmlContent, 'strict');
    
    expect(mockDOMPurify.sanitize).toHaveBeenCalledWith(
      htmlContent,
      expect.objectContaining({
        ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'span'],
        ALLOWED_ATTR: ['class'],
      })
    );
  });

  it('should use rich config for rich level', () => {
    const htmlContent = '<p>Content</p>';
    sanitizeHtml(htmlContent, 'rich');
    
    expect(mockDOMPurify.sanitize).toHaveBeenCalledWith(
      htmlContent,
      expect.objectContaining({
        ALLOWED_TAGS: expect.arrayContaining(['img', 'blockquote', 'code']),
        ALLOWED_ATTR: expect.arrayContaining(['src', 'alt', 'title']),
      })
    );
  });
});

describe('sanitizeText', () => {
  it('should return empty string for null/undefined input', () => {
    expect(sanitizeText('')).toBe('');
    expect(sanitizeText(null as any)).toBe('');
    expect(sanitizeText(undefined as any)).toBe('');
  });

  it('should escape HTML entities', () => {
    const text = '<script>alert("xss")</script>';
    const result = sanitizeText(text);
    
    expect(result).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;&#x2F;script&gt;');
  });

  it('should escape all dangerous characters', () => {
    const text = `&<>"'/`;
    const result = sanitizeText(text);
    
    expect(result).toBe('&amp;&lt;&gt;&quot;&#x27;&#x2F;');
  });
});

describe('isSafeUrl', () => {
  it('should return false for null/undefined/empty URLs', () => {
    expect(isSafeUrl('')).toBe(false);
    expect(isSafeUrl(null as any)).toBe(false);
    expect(isSafeUrl(undefined as any)).toBe(false);
  });

  it('should allow safe protocols', () => {
    expect(isSafeUrl('https://example.com')).toBe(true);
    expect(isSafeUrl('http://example.com')).toBe(true);
    expect(isSafeUrl('mailto:test@example.com')).toBe(true);
    expect(isSafeUrl('tel:+1234567890')).toBe(true);
  });

  it('should allow relative URLs', () => {
    expect(isSafeUrl('/path/to/page')).toBe(true);
    expect(isSafeUrl('./relative/path')).toBe(true);
    expect(isSafeUrl('../parent/path')).toBe(true);
  });

  it('should block dangerous protocols', () => {
    expect(isSafeUrl('javascript:alert("xss")')).toBe(false);
    expect(isSafeUrl('data:text/html,<script>alert("xss")</script>')).toBe(false);
    expect(isSafeUrl('vbscript:msgbox("xss")')).toBe(false);
    expect(isSafeUrl('file:///etc/passwd')).toBe(false);
  });

  it('should be case insensitive', () => {
    expect(isSafeUrl('JAVASCRIPT:alert("xss")')).toBe(false);
    expect(isSafeUrl('HTTPS://example.com')).toBe(true);
  });
});

describe('SafeHtml component', () => {
  beforeEach(() => {
    // Mock browser environment for React components
    Object.defineProperty(global, 'window', {
      value: {},
      writable: true,
    });
  });

  it('should render sanitized HTML content', () => {
    mockDOMPurify.sanitize.mockReturnValue('<p>Safe content</p>');
    
    render(<SafeHtml html="<p>Safe content</p>" />);
    
    expect(mockDOMPurify.sanitize).toHaveBeenCalled();
  });

  it('should apply custom className', () => {
    mockDOMPurify.sanitize.mockReturnValue('<p>Content</p>');
    
    const { container } = render(
      <SafeHtml html="<p>Content</p>" className="custom-class" />
    );
    
    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('should use custom tag', () => {
    mockDOMPurify.sanitize.mockReturnValue('<p>Content</p>');
    
    const { container } = render(
      <SafeHtml html="<p>Content</p>" tag="section" />
    );
    
    expect(container.firstChild?.nodeName).toBe('SECTION');
  });

  it('should pass correct security level to sanitizer', () => {
    render(<SafeHtml html="<p>Content</p>" level="strict" />);
    
    expect(mockDOMPurify.sanitize).toHaveBeenCalledWith(
      '<p>Content</p>',
      expect.objectContaining({
        ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'span'],
      })
    );
  });
});

describe('SafeText component', () => {
  it('should render plain text safely', () => {
    render(<SafeText text="<script>alert('xss')</script>" />);
    
    // React automatically escapes the content, so we expect the literal text
    expect(screen.getByText("<script>alert('xss')</script>")).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <SafeText text="Content" className="custom-class" />
    );
    
    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('should use custom tag', () => {
    const { container } = render(
      <SafeText text="Content" tag="p" />
    );
    
    expect(container.firstChild?.nodeName).toBe('P');
  });
});

describe('SafeLink component', () => {
  it('should render link for safe URLs', () => {
    render(
      <SafeLink href="https://example.com" data-testid="safe-link">
        Click me
      </SafeLink>
    );
    
    const link = screen.getByTestId('safe-link');
    expect(link).toBeInTheDocument();
    expect(link.tagName).toBe('A');
    expect(link).toHaveAttribute('href', 'https://example.com');
  });

  it('should render span for unsafe URLs', () => {
    render(
      <SafeLink href="javascript:alert('xss')" data-testid="unsafe-link">
        Click me
      </SafeLink>
    );
    
    const element = screen.getByTestId('unsafe-link');
    expect(element.tagName).toBe('SPAN');
    expect(element).not.toHaveAttribute('href');
  });

  it('should add noopener noreferrer for target="_blank"', () => {
    render(
      <SafeLink 
        href="https://example.com" 
        target="_blank"
        data-testid="blank-link"
      >
        Click me
      </SafeLink>
    );
    
    const link = screen.getByTestId('blank-link');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('should not add rel attribute for other targets', () => {
    render(
      <SafeLink 
        href="https://example.com" 
        target="_self"
        data-testid="self-link"
      >
        Click me
      </SafeLink>
    );
    
    const link = screen.getByTestId('self-link');
    expect(link).not.toHaveAttribute('rel');
  });

  it('should pass through other props', () => {
    render(
      <SafeLink 
        href="https://example.com" 
        className="custom-class"
        data-testid="props-link"
        title="Test title"
      >
        Click me
      </SafeLink>
    );
    
    const link = screen.getByTestId('props-link');
    expect(link).toHaveClass('custom-class');
    expect(link).toHaveAttribute('title', 'Test title');
  });
});

describe('XSS Prevention Integration Tests', () => {
  beforeEach(() => {
    Object.defineProperty(global, 'window', {
      value: {},
      writable: true,
    });
  });

  it('should prevent script injection via SafeHtml', () => {
    const maliciousHtml = '<p>Safe content</p><script>alert("xss")</script>';
    
    // Mock DOMPurify to simulate real behavior
    mockDOMPurify.sanitize.mockReturnValue('<p>Safe content</p>');
    
    render(<SafeHtml html={maliciousHtml} />);
    
    expect(mockDOMPurify.sanitize).toHaveBeenCalledWith(
      maliciousHtml,
      expect.objectContaining({
        FORBID_TAGS: expect.arrayContaining(['script']),
      })
    );
  });

  it('should prevent event handler injection', () => {
    const maliciousHtml = '<div onclick="alert(\'xss\')">Click me</div>';
    
    render(<SafeHtml html={maliciousHtml} />);
    
    expect(mockDOMPurify.sanitize).toHaveBeenCalledWith(
      maliciousHtml,
      expect.objectContaining({
        FORBID_ATTR: expect.arrayContaining(['onclick']),
      })
    );
  });

  it('should prevent javascript: URLs in links', () => {
    render(
      <SafeLink href="javascript:alert('xss')" data-testid="js-link">
        Malicious Link
      </SafeLink>
    );
    
    const element = screen.getByTestId('js-link');
    expect(element.tagName).toBe('SPAN'); // Should render as span, not link
  });

  it('should handle mixed content safely', () => {
    const mixedContent = `
      <p>Regular content</p>
      <script>alert('xss')</script>
      <img src="x" onerror="alert('xss')">
      <a href="javascript:alert('xss')">Link</a>
    `;
    
    // Mock DOMPurify to strip dangerous content
    mockDOMPurify.sanitize.mockReturnValue('<p>Regular content</p>');
    
    render(<SafeHtml html={mixedContent} level="basic" />);
    
    expect(mockDOMPurify.sanitize).toHaveBeenCalledWith(
      mixedContent,
      expect.objectContaining({
        FORBID_TAGS: expect.arrayContaining(['script']),
        FORBID_ATTR: expect.arrayContaining(['onerror']),
      })
    );
  });
});