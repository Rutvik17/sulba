import type { AstroUserConfig } from 'astro';
import { fontProviders } from 'astro/config';

// Fonts come from the Fontsource packages in node_modules, never a CDN, and are served from
// sulba.dev (decision record 11). Each @font-face carries a unicode-range, so a browser
// downloads only the files for the characters on the page.
const npm = fontProviders.npm({ remote: false });

export const fonts: NonNullable<AstroUserConfig['fonts']> = [
  {
    provider: npm,
    name: 'Geist Variable',
    cssVariable: '--font-sans',
    weights: ['100 900'],
    fallbacks: ['sans-serif'],
  },
  {
    provider: npm,
    name: 'Geist Mono Variable',
    cssVariable: '--font-mono',
    weights: ['100 900'],
    fallbacks: ['monospace'],
  },
  {
    provider: npm,
    name: 'Instrument Serif',
    cssVariable: '--font-display',
    weights: [400],
    styles: ['normal'],
    fallbacks: ['serif'],
  },
];
