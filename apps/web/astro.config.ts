import cloudflare from '@astrojs/cloudflare';
import { defineConfig } from 'astro/config';
import { fonts } from './fonts';

export default defineConfig({
  site: 'https://sulba.dev',
  // Images are optimised at build time, so the Worker needs no Cloudflare Images binding.
  adapter: cloudflare({ imageService: 'compile' }),
  // Sign-in lives in Supabase, so Astro sessions and the KV namespace they create stay off.
  session: false,
  fonts,
});
