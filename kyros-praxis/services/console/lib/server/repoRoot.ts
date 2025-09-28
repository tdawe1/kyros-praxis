import path from 'path';
import fs from 'fs';

// Get the root directory of the repository
export function getRepoRoot(): string {
  // Start from the current directory (console service)
  let currentDir = process.cwd();
  
  // Go up directories until we find the root (containing .git or specific markers)
  while (currentDir !== '/') {
    if (fs.existsSync(path.join(currentDir, '.git')) ||
        fs.existsSync(path.join(currentDir, 'kyros-praxis'))) {
      return currentDir;
    }
    const parentDir = path.dirname(currentDir);
    if (parentDir === currentDir) break; // Reached root
    currentDir = parentDir;
  }
  
  // Fallback to current directory structure
  return path.resolve(process.cwd(), '../..');
}

// Get the devlogs directory path
export function devlogsDir(): string {
  return path.join(getRepoRoot(), 'devlogs');
}

// Get a file path relative to repo root
export function repoFile(relativePath: string): string {
  return path.join(getRepoRoot(), relativePath);
}

// Check if a file exists in the repo
export function repoFileExists(relativePath: string): boolean {
  return fs.existsSync(repoFile(relativePath));
}

// Read a file from the repo
export function readRepoFile(relativePath: string, encoding: BufferEncoding = 'utf8'): string {
  return fs.readFileSync(repoFile(relativePath), encoding);
}