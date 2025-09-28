/**
 * Repository root path utilities
 */

import path from 'path';

/**
 * Get the repository root path
 */
export function getRepoRoot(): string {
  // Start from current directory and walk up to find the root
  let currentDir = __dirname;
  
  while (currentDir !== '/' && currentDir !== '') {
    // Look for common repository root indicators
    try {
      const pkg = require(path.join(currentDir, 'package.json'));
      if (pkg.name === 'kyros-console' || currentDir.endsWith('kyros-praxis')) {
        return currentDir;
      }
    } catch {
      // Continue searching
    }
    
    const parentDir = path.dirname(currentDir);
    if (parentDir === currentDir) break; // Reached root
    currentDir = parentDir;
  }
  
  // Fallback to assuming we're in services/console
  return path.resolve(__dirname, '../../..');
}

/**
 * Get path relative to repository root
 */
export function getRepoPath(...paths: string[]): string {
  return path.join(getRepoRoot(), ...paths);
}