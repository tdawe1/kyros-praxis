import path from 'path';

export const repoRoot = path.resolve(process.cwd(), '../..');
export const devlogsDir = path.join(repoRoot, 'devlogs');
export const repoFile = (filename: string) => path.join(repoRoot, filename);