// The characters the site's math font has a glyph for (decision record 15).
import { createRequire } from 'node:module';
import { openSync } from 'fontkit';

export function mathFontCharacters(): Set<number> {
  const path = createRequire(import.meta.url).resolve('@sulba/ui/fonts/noto-sans-math.woff2');
  const font = openSync(path);
  if (!('characterSet' in font)) throw new Error(`${path} holds several fonts, not one.`);
  return new Set(font.characterSet);
}
