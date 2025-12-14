import '@testing-library/jest-dom/vitest';

import { mkdirSync } from 'node:fs';
import { join } from 'node:path';

const localTmp = join(process.cwd(), '.vitest-tmp');

try {
  mkdirSync(localTmp, { recursive: true });
} catch {
  // directory already exists or cannot be created; ignore so tests can proceed
}
