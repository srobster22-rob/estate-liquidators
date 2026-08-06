import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  build: { target: 'es2020', reportCompressedSize: true },
  test: { globals: true, environment: 'node', include: ['test/**/*.test.ts'] },
});
