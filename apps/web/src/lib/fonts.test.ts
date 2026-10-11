import { existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { expect, test } from 'vitest';
import { facesIn, variants } from '../../fonts';

const require = createRequire(import.meta.url);

test('a face is read as its WOFF2 file, weight, style and scripts', () => {
  const css = `/* instrument-serif-latin-400-normal */
@font-face {
  font-family: 'Instrument Serif';
  font-style: normal;
  font-display: swap;
  font-weight: 400;
  src: url(./files/instrument-serif-latin-400-normal.woff2) format('woff2'), url(./files/instrument-serif-latin-400-normal.woff) format('woff');
  unicode-range: U+0000-00FF,U+0131,U+0152-0153;
}`;

  expect(facesIn(css, '@fontsource/instrument-serif')).toEqual([
    {
      src: ['@fontsource/instrument-serif/files/instrument-serif-latin-400-normal.woff2'],
      weight: '400',
      style: 'normal',
      display: 'swap',
      unicodeRange: ['U+0000-00FF', 'U+0131', 'U+0152-0153'],
    },
  ]);
});

test('every font is a file in an installed package, never a web address', () => {
  const families = [
    variants('@fontsource-variable/geist', 'wght.css'),
    variants('@fontsource-variable/geist-mono', 'wght.css'),
    variants('@fontsource/instrument-serif', '400.css'),
  ];

  for (const family of families) {
    for (const { src } of family) {
      expect(src[0]).toMatch(/^@fontsource(-variable)?\/[\w-]+\/files\/[\w-]+\.woff2$/);
      expect(existsSync(require.resolve(src[0]))).toBe(true);
    }
  }
});
