/// <reference types="vitest/config" />
import { getViteConfig } from 'astro/config';
import { fonts } from './fonts';

export default getViteConfig(
  {
    test: {
      include: ['src/**/*.test.ts'],
    },
  },
  // Component tests render without the Cloudflare adapter, whose dev server can't run inside Vitest,
  // so astro.config.ts isn't loaded; the fonts the layout needs are passed here instead.
  // The end-to-end tests cover the real Worker.
  { configFile: false, fonts },
);
