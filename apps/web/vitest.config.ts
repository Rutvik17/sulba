/// <reference types="vitest/config" />
import { getViteConfig } from 'astro/config';
import { fonts } from './fonts';

// Astro types a font family's provider options only inside defineConfig; its inline config takes
// the same families without them.
type InlineConfig = NonNullable<Parameters<typeof getViteConfig>[1]>;

export default getViteConfig(
  {
    test: {
      include: ['src/**/*.test.ts'],
    },
  },
  // Component tests render without the Cloudflare adapter, whose dev server can't run inside Vitest,
  // so astro.config.ts isn't loaded; the fonts the layout needs are passed here instead.
  // The end-to-end tests cover the real Worker.
  { configFile: false, fonts: fonts as unknown as NonNullable<InlineConfig['fonts']> },
);
