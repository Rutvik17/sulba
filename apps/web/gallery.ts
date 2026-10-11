import type { AstroIntegration } from 'astro';

/**
 * The component gallery, at /gallery/, is for building the site. `astro dev` serves it, and so do
 * builds that set SULBA_GALLERY=on: the end-to-end tests and branch previews. sulba.dev never has it.
 */
export function gallery(requested = process.env.SULBA_GALLERY === 'on'): AstroIntegration {
  return {
    name: 'sulba:gallery',
    hooks: {
      'astro:config:setup': ({ command, injectRoute }) => {
        if (command !== 'dev' && !requested) return;
        injectRoute({
          pattern: '/gallery',
          entrypoint: new URL('./src/gallery/index.astro', import.meta.url),
        });
      },
    },
  };
}
