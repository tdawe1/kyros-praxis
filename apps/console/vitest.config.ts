import { defineConfig } from 'vitest/config';

export default defineConfig({
  cacheDir: './node_modules/.vitest',
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    globals: false,
    css: true,
  },
  esbuild: {
    jsx: 'automatic',
    jsxDev: true,
  },
});
