import cloudflare from '@astrojs/cloudflare';
import { defineConfig, envField } from 'astro/config';
import { fonts } from './fonts';

export default defineConfig({
  site: 'https://sulba.dev',
  // Images are optimised at build time, so the Worker needs no Cloudflare Images binding.
  adapter: cloudflare({ imageService: 'compile' }),
  // Sign-in lives in Supabase, so Astro sessions and the KV namespace they create stay off.
  session: false,
  fonts,
  env: {
    schema: {
      // Turnstile's site key is public. Its default is Cloudflare's test key, which always passes,
      // so development, tests and previews need no setup; production builds set the real one.
      PUBLIC_TURNSTILE_SITE_KEY: envField.string({
        context: 'client',
        access: 'public',
        default: '1x00000000000000000000AA',
      }),
      // The contact form's secrets are Worker secrets, read when a message is sent. Without all
      // four the form answers that it can't send, and never sends unchecked.
      RESEND_API_KEY: envField.string({ context: 'server', access: 'secret', optional: true }),
      CONTACT_TO: envField.string({ context: 'server', access: 'secret', optional: true }),
      CONTACT_FROM: envField.string({ context: 'server', access: 'secret', optional: true }),
      TURNSTILE_SECRET_KEY: envField.string({
        context: 'server',
        access: 'secret',
        optional: true,
      }),
    },
  },
});
