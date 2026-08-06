import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  build: {
    target: 'es2020',
    // The byte budget in the brief is the point, not a nicety. scripts/check-budget.ts asserts it.
    assetsInlineLimit: 0,
    reportCompressedSize: true,
  },
  test: {
    globals: true,
    environment: 'node',
    include: ['test/**/*.test.ts'],
  },
});
