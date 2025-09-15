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
  return path.join(root, ...segments);
}

