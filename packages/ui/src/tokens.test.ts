import { readFileSync } from 'node:fs';
import { describe, expect, test } from 'vitest';
import { composite, contrast, parseColour } from './contrast';

const css = readFileSync(new URL('./tokens.css', import.meta.url), 'utf8');

/** The custom properties declared in the block that `selector` opens. */
function block(selector: string): Map<string, string> {
  const start = css.indexOf(`${selector} {`);
  if (start === -1) throw new Error(`tokens.css has no block for ${selector}`);
  const body = css.slice(css.indexOf('{', start) + 1, css.indexOf('}', start));
  return new Map(
    [...body.matchAll(/--([\w-]+):\s*([^;]+);/g)].map(([, name = '', value = '']) => [
      name,
      value.trim(),
    ]),
  );
}

const themes = {
  dark: block(':root[data-theme="dark"]'),
  light: block(':root[data-theme="light"]'),
};
const grounds = ['bg', 'surface', 'raise'];
const text = ['fg', 'dim', 'accent', 'ok', 'bad'];

test('following a light device setting gives the same colours as picking the light theme', () => {
  expect(block(':root:not([data-theme])')).toEqual(themes.light);
});

test('both themes define the same colours', () => {
  expect([...themes.light.keys()]).toEqual([...themes.dark.keys()]);
});

describe.each(Object.entries(themes))('the %s theme', (_, colours) => {
  const colour = (name: string): string => {
    const value = colours.get(name);
    if (value === undefined) throw new Error(`no --${name}`);
    return value;
  };

  test.each(grounds.flatMap((ground) => text.map((fg) => [fg, ground])))(
    '--%s text on --%s meets 4.5:1',
    (fg, ground) => {
      const ratio = contrast(parseColour(colour(fg)).rgb, parseColour(colour(ground)).rgb);
      expect(ratio).toBeGreaterThanOrEqual(4.5);
    },
  );

  test.each(grounds)('a control edge on --%s meets 3:1', (ground) => {
    const edge = composite(colour('line-strong'), colour(ground));
    expect(contrast(edge, parseColour(colour(ground)).rgb)).toBeGreaterThanOrEqual(3);
  });
});
