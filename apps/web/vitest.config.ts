/// <reference types="vitest/config" />
import { getViteConfig } from 'astro/config';

export default getViteConfig(
  {
    test: {
      include: ['src/**/*.test.ts'],
    },
  },
  // Component tests render without the Cloudflare adapter, whose dev server can't run inside Vitest.
  // The end-to-end tests cover the real Worker.
  { configFile: false },
);
