import { fileURLToPath } from 'node:url';
import type { AstroIntegration } from 'astro';
import { build } from 'vite';

const root = fileURLToPath(new URL('../app/', import.meta.url));

/**
 * The app, apps/app, is served from the site's Worker under /app/ (decision record 47). Each build
 * of the site builds it with Vite, into the site's own files.
 */
export function app(): AstroIntegration {
  return {
    name: 'sulba:app',
    hooks: {
      'astro:build:done': async ({ dir }) => {
        await build({
          root,
          configFile: `${root}vite.config.ts`,
          logLevel: 'warn',
          build: { outDir: fileURLToPath(new URL('./app/', dir)), emptyOutDir: true },
        });
      },
    },
  };
}
