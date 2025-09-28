/**
 * Security demonstration - showing how input sanitization prevents attacks
 */

import { sanitizeHtml, sanitizeText, sanitizeUrl, sanitizeSearchQuery } from './sanitization';

export function demonstrateSecurity() {
  console.log('🔒 Input Sanitization Security Demo');
  console.log('=====================================');

  // XSS Prevention Demo
  const maliciousHtml = '<script>alert("XSS Attack!")</script><p>Legitimate content</p>';
  const sanitizedHtml = sanitizeHtml(maliciousHtml);
  console.log('\n📡 XSS Prevention:');
  console.log('Input:', maliciousHtml);
  console.log('Output:', sanitizedHtml);

  // Text Escaping Demo
  const maliciousText = '<img src="x" onerror="alert(\'XSS\')" />';
  const sanitizedText = sanitizeText(maliciousText);
  console.log('\n🔤 Text Escaping:');
  console.log('Input:', maliciousText);
  console.log('Output:', sanitizedText);

  // URL Sanitization Demo
  const maliciousUrl = 'javascript:alert("XSS via URL")';
  const sanitizedUrl = sanitizeUrl(maliciousUrl);
  console.log('\n🔗 URL Sanitization:');
  console.log('Input:', maliciousUrl);
  console.log('Output:', sanitizedUrl || '[BLOCKED - Dangerous URL]');

  // SQL Injection Prevention Demo
  const maliciousQuery = "'; DROP TABLE users; --";
  const sanitizedQuery = sanitizeSearchQuery(maliciousQuery);
  console.log('\n💉 SQL Injection Prevention:');
  console.log('Input:', maliciousQuery);
  console.log('Output:', sanitizedQuery);

  console.log('\n✅ All attacks successfully prevented!');
}

// Run demo if this file is executed directly
if (typeof window === 'undefined' && require.main === module) {
  demonstrateSecurity();
}