import fs from 'fs';
import path from 'path';

/**
 * Resolve the repository root by walking upward until a marker is found.
 * Markers: .git directory or afkimplement1.md file at repo root.
 */
export function resolveRepoRoot(startDir?: string): string {
  let dir = startDir || process.cwd();
  // Limit climb to avoid infinite loops
  for (let i = 0; i < 10; i++) {
    const gitPath = path.join(dir, '.git');
    const markerPath = path.join(dir, 'afkimplement1.md');
    if (fs.existsSync(gitPath) || fs.existsSync(markerPath)) {
      return dir;
    }
    const parent = path.dirname(dir);
    if (!parent || parent === dir) break;
    dir = parent;
  }
  return startDir || process.cwd();
}

export function devlogsDir(): string {
  const root = resolveRepoRoot();
  const devlogs = path.join(root, '.devlogs');
  if (!fs.existsSync(devlogs)) {
    fs.mkdirSync(devlogs, { recursive: true });
  }
  return devlogs;
}

export function repoFile(...segments: string[]): string {
  const root = resolveRepoRoot();
  
  // Validate and sanitize path segments to prevent path traversal
  const sanitizedSegments = segments.filter(segment => {
    // Reject empty segments, null, or undefined
    if (!segment || segment.trim() === '') {
      return false;
    }
    
    // Decode URL-encoded characters to catch encoded traversal attempts
    let decodedSegment = segment;
    try {
      decodedSegment = decodeURIComponent(segment);
    } catch {
      // If decoding fails, use original segment
    }
    
    // Reject segments containing path traversal patterns (both original and decoded)
    const pathTraversalPatterns = ['..', './', '.\\', '..\\'];
    for (const pattern of pathTraversalPatterns) {
      if (segment.includes(pattern) || decodedSegment.includes(pattern)) {
        throw new Error(`Invalid path segment: ${segment}`);
      }
    }
    
    // Reject absolute paths (check both original and decoded)
    if (path.isAbsolute(segment) || path.isAbsolute(decodedSegment)) {
      throw new Error(`Absolute paths not allowed: ${segment}`);
    }
    
    // Reject Windows drive letters (e.g., C:, D:)
    if (/^[a-zA-Z]:/.test(segment) || /^[a-zA-Z]:/.test(decodedSegment)) {
      throw new Error(`Absolute paths not allowed: ${segment}`);
    }
    
    return true;
  });
  
  // Join the sanitized segments
  const requestedPath = path.join(root, ...sanitizedSegments);
  
  // Ensure the resolved path is still within the repository root
  const resolvedPath = path.resolve(requestedPath);
  const resolvedRoot = path.resolve(root);
  
  if (!resolvedPath.startsWith(resolvedRoot + path.sep) && resolvedPath !== resolvedRoot) {
    throw new Error(`Path traversal attempt detected: ${segments.join('/')}`);
  }
  
  return resolvedPath;
}

