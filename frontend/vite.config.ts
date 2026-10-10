import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';

export default defineConfig(({ command }) => ({
  plugins: [react(), {
    name: 'development-csp',
    transformIndexHtml(html) {
      // Vite injects development styles and refresh preamble. Production remains strict.
      return command === 'serve' ? html.replace("style-src 'self'", "style-src 'self' 'unsafe-inline'").replace("script-src 'self'", "script-src 'self' 'unsafe-inline'") : html;
    },
  }],
  server: { fs: { strict: true, allow: [fileURLToPath(new URL('./', import.meta.url))], deny: ['.env', '.env.*', '*.pem', '*.key', '**/.git/**', '**/.local/**'] } },
  test: { environment: 'jsdom', setupFiles: ['./tests/setup.ts'], include: ['tests/**/*.test.tsx', 'tests/**/*.test.ts'] },
}));
