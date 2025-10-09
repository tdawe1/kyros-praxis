import path from 'path';

/**
 * Sanitizes path segments to prevent directory traversal attacks.
 * Removes or normalizes dangerous patterns like '../', absolute paths, etc.
 */
export function sanitizePathSegment(segment: string): string {
  if (typeof segment !== 'string') {
    throw new Error('Path segment must be a string');
  }

  // Remove null bytes that could terminate string prematurely
  let cleaned = segment.replace(/\0/g, '');

  // Remove .. sequences completely
  cleaned = cleaned.replace(/\.\./g, '');
  
  // Prevent absolute paths on Windows (remove drive letters and colon) - do this before removing invalid chars
  cleaned = cleaned.replace(/^[a-zA-Z]:/, '');
  
  // Remove invalid filename characters (including colon if any remain)
  cleaned = cleaned.replace(/[<>:"|?*]/g, '');
  
  // Remove leading/trailing slashes
  cleaned = cleaned.replace(/^\/+|\/+$/g, '');

  // Remove any remaining path separators from the beginning
  cleaned = cleaned.replace(/^[\/\\]+/, '');

  // Ensure the segment is not empty after cleaning
  if (!cleaned || cleaned.trim() === '') {
    throw new Error('Invalid path segment: cannot be empty after sanitization');
  }

  return cleaned;
}

/**
 * Sanitizes multiple path segments and joins them safely.
 * Each segment is individually sanitized before joining.
 */
export function sanitizeAndJoinPaths(basePath: string, ...segments: string[]): string {
  if (typeof basePath !== 'string') {
    throw new Error('Base path must be a string');
  }

  // Check for path traversal patterns BEFORE sanitization
  const hasTraversalPattern = segments.some(segment => 
    typeof segment === 'string' && segment.includes('..')
  );
  
  if (hasTraversalPattern) {
    throw new Error('Path traversal attempt detected: .. sequences are not allowed');
  }

  // Sanitize each segment
  const cleanSegments = segments.map(segment => sanitizePathSegment(segment));

  // Join with the base path
  const resultPath = path.join(basePath, ...cleanSegments);

  // Ensure the result path is still within the base directory
  const normalizedResult = path.normalize(resultPath);
  const normalizedBase = path.normalize(basePath);

  if (!normalizedResult.startsWith(normalizedBase)) {
    throw new Error('Path traversal attempt detected: resulting path is outside base directory');
  }

  return resultPath;
}

/**
 * Validates that a filename is safe and doesn't contain path traversal patterns.
 * Used for simple filename validation without directory structure.
 */
export function validateFilename(filename: string): string {
  if (typeof filename !== 'string') {
    throw new Error('Filename must be a string');
  }

  // Check for path traversal patterns
  if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
    throw new Error('Filename cannot contain path traversal patterns or directory separators');
  }

  // Remove null bytes
  const cleaned = filename.replace(/\0/g, '');

  // Check for invalid characters
  if (cleaned.match(/[<>:"|?*]/)) {
    throw new Error('Filename contains invalid characters');
  }

  // Ensure not empty
  if (!cleaned || cleaned.trim() === '') {
    throw new Error('Filename cannot be empty');
  }

  return cleaned;
}