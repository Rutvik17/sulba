// The gallery's formulas render, and the math font draws every character in them. The gallery is
// prerendered in workerd, which can't read the font, so the check runs here.
import { readFile } from 'node:fs/promises';
import { drawnCharacters, renderProse } from '@sulba/content';
import { mathFontCharacters } from '@sulba/content/math-font';
import { expect, test } from 'vitest';

const text = await readFile(new URL('./formulas.md', import.meta.url), 'utf8');

test('the gallery’s formulas render without errors', () => {
  const { errors, formulas } = renderProse(text, {});
  expect(errors).toEqual([]);
  expect(formulas.length).toBeGreaterThanOrEqual(7);
});

test('the math font has every character the gallery’s formulas draw', () => {
  const font = mathFontCharacters();
  const missing = renderProse(text, {})
    .formulas.flatMap((formula) => [...drawnCharacters(formula)])
    .filter((point) => !font.has(point))
    .map((point) => String.fromCodePoint(point));
  expect(missing).toEqual([]);
});
