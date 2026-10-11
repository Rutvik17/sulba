import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fontProviders } from 'astro/config';

// Fonts come from the Fontsource packages in node_modules and are served from sulba.dev
// (decision record 11). The files are read from disk, so a build never fetches a font. Each
// package's own stylesheet lists a file per script with its unicode-range, so a browser downloads
// only the files for the characters on the page.
const require = createRequire(import.meta.url);
const local = fontProviders.local();

export interface Variant {
  src: [string];
  weight: string;
  style: 'normal' | 'italic';
  display: 'swap';
  unicodeRange: [string, ...string[]];
}

/** The @font-face rules in a Fontsource stylesheet, each as its WOFF2 file in the package. */
export function facesIn(css: string, pkg: string): Variant[] {
  return [...css.matchAll(/@font-face\s*\{([^}]*)\}/g)].map(([, face = '']) => {
    const read = (pattern: RegExp, what: string) => {
      const value = pattern.exec(face)?.[1]?.trim();
      if (!value) throw new Error(`A @font-face in ${pkg} has no ${what}`);
      return value;
    };
    const style = read(/font-style:\s*([^;]+);/, 'font-style');
    if (style !== 'normal' && style !== 'italic')
      throw new Error(`A @font-face in ${pkg} has a font-style of ${style}`);
    const [first = '', ...rest] = read(/unicode-range:\s*([^;]+);/, 'unicode-range').split(',');
    return {
      src: [`${pkg}/files/${read(/url\(\.\/files\/([^)]+\.woff2)\)/, 'WOFF2 file')}`],
      weight: read(/font-weight:\s*([^;]+);/, 'font-weight'),
      style,
      display: 'swap',
      unicodeRange: [first, ...rest],
    };
  });
}

/** The fonts one of a Fontsource package's stylesheets lists, read from node_modules. */
export function variants(pkg: string, stylesheet: string): [Variant, ...Variant[]] {
  const css = readFileSync(require.resolve(`${pkg}/${stylesheet}`), 'utf8');
  const [head, ...tail] = facesIn(css, pkg);
  if (!head) throw new Error(`${pkg}/${stylesheet} has no @font-face`);
  return [head, ...tail];
}

export const fonts = [
  {
    provider: local,
    name: 'Geist Variable',
    cssVariable: '--font-sans',
    fallbacks: ['sans-serif'],
    options: { variants: variants('@fontsource-variable/geist', 'wght.css') },
  },
  {
    provider: local,
    name: 'Geist Mono Variable',
    cssVariable: '--font-mono',
    fallbacks: ['monospace'],
    options: { variants: variants('@fontsource-variable/geist-mono', 'wght.css') },
  },
  {
    provider: local,
    name: 'Instrument Serif',
    cssVariable: '--font-display',
    fallbacks: ['serif'],
    options: { variants: variants('@fontsource/instrument-serif', '400.css') },
  },
];
