import { expect, test } from 'vitest';
import { composite, contrast, parseColour } from './contrast';

test('black on white has the highest contrast WCAG defines, and a colour on itself the lowest', () => {
  expect(contrast([0, 0, 0], [255, 255, 255])).toBeCloseTo(21, 10);
  expect(contrast([118, 118, 118], [118, 118, 118])).toBe(1);
});

test('#767676 on white comes to 4.54:1, the lightest grey that passes for text', () => {
  expect(contrast(parseColour('#767676').rgb, [255, 255, 255])).toBeCloseTo(4.54, 2);
});

test('a translucent colour mixes with the ground beneath it', () => {
  expect(parseColour('rgb(0 0 0 / 0.5)')).toEqual({ rgb: [0, 0, 0], alpha: 0.5 });
  expect(composite('rgb(0 0 0 / 0.5)', '#ffffff')).toEqual([127.5, 127.5, 127.5]);
});

test('a colour in any other format is refused', () => {
  expect(() => parseColour('red')).toThrow('Not a #rrggbb or rgb() colour: red');
});
