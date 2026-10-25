import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// Production builds get a strict Content-Security-Policy. Dev mode is left
// without one because Vite's hot reload relies on an inline script.
function cspPlugin(apiBase) {
  const policy = [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    'font-src https://fonts.gstatic.com',
    "img-src 'self' data:",
    `connect-src 'self' ${apiBase}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; ');
  return {
    name: 'travel-partner-csp',
    apply: 'build',
    transformIndexHtml: () => [
      { tag: 'meta', attrs: { 'http-equiv': 'Content-Security-Policy', content: policy }, injectTo: 'head-prepend' },
    ],
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');
  const apiBase = env.VITE_API_BASE_URL || 'http://localhost:8000';
  return {
    plugins: [react(), cspPlugin(apiBase)],
    // Only VITE_-prefixed variables reach the bundle; keep secrets out of them.
    envPrefix: 'VITE_',
    server: { port: 5173, strictPort: true },
    build: { sourcemap: false },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: './tests/setup.js',
      include: ['tests/**/*.test.{js,jsx}'],
    },
  };
});
