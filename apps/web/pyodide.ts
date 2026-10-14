import { createReadStream } from 'node:fs';
import { cp, stat } from 'node:fs/promises';
import { extname, join, relative } from 'node:path';
import { assemblePyodide, pyodideFolder } from '@sulba/lab/assemble';
import { pyodidePath } from '@sulba/lab/protocol';
import type { AstroIntegration } from 'astro';

const types: Record<string, string> = {
  '.mjs': 'text/javascript',
  '.wasm': 'application/wasm',
  '.json': 'application/json',
  '.zip': 'application/zip',
  '.whl': 'application/zip',
};

/**
 * Pyodide runs learners' Python from sulba.dev's own files (decision record 17). This puts them
 * together before the site starts, serves them at `pyodidePath` while developing, and copies them
 * into each build.
 */
export function pyodide(): AstroIntegration {
  return {
    name: 'sulba:pyodide',
    hooks: {
      'astro:config:setup': async ({ updateConfig }) => {
        await assemblePyodide();
        updateConfig({
          vite: {
            plugins: [
              {
                name: 'sulba:pyodide',
                configureServer(server) {
                  server.middlewares.use(pyodidePath, async (request, response, next) => {
                    const name = decodeURIComponent((request.url ?? '/').split('?')[0] ?? '/');
                    const path = join(pyodideFolder, name);
                    const inside = !relative(pyodideFolder, path).startsWith('..');
                    const found = inside && (await stat(path).catch(() => null))?.isFile();
                    if (!found) return next();
                    const type = types[extname(path)];
                    if (type) response.setHeader('Content-Type', type);
                    createReadStream(path).pipe(response);
                  });
                },
              },
            ],
          },
        });
      },
      'astro:build:done': async ({ dir }) => {
        await cp(pyodideFolder, new URL(`.${pyodidePath}`, dir), { recursive: true });
      },
    },
  };
}
