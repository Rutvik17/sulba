/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// The app is served from the site's Worker under /app/ (decision record 47). While developing, Vite
// serves it and passes every other address, sign-in included, to the site's own dev server, so the
// two share an origin, and with it the session.
export default defineConfig({
  base: '/app/',
  // Supabase's address and publishable key are public, as on the site (astro.config.ts).
  envPrefix: 'PUBLIC_',
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 4323,
    strictPort: true,
    proxy: { '^/(?!app(/|$))': { target: 'http://127.0.0.1:4321', ws: true } },
  },
  test: {
    include: ['src/**/*.test.ts'],
  },
});
