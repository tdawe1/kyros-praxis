import { headers } from 'next/headers';

/**
 * Get the CSP nonce for the current request
 * This nonce is generated in middleware.ts and passed via headers
 */
export function getNonce(): string {
  const headersList = headers();
  return headersList.get('x-nonce') || '';
}

/**
 * Generate CSP script-src directive with nonce
 */
export function getScriptSrcWithNonce(nonce: string, isDevelopment: boolean): string {
  const base = `'self' 'nonce-${nonce}'`;
  return isDevelopment ? `${base} 'unsafe-eval'` : base;
}

/**
 * Generate CSP style-src directive with nonce
 */
export function getStyleSrcWithNonce(nonce: string, isDevelopment: boolean): string {
  const base = `'self' 'nonce-${nonce}'`;
  return isDevelopment ? `${base} 'unsafe-inline'` : base;
}