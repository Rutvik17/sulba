import { expect, test } from 'vitest';
import { cordPath, pegs } from './mark';

type Point = (typeof pegs)[number];

const [top, corner, end] = pegs;
const distance = (a: Point, b: Point) => Math.hypot(b[0] - a[0], b[1] - a[1]);

test('the cord makes sides in the ratio 3 : 4 : 5', () => {
  const unit = distance(top, corner) / 3;

  expect(distance(corner, end) / unit).toBeCloseTo(4, 10);
  expect(distance(end, top) / unit).toBeCloseTo(5, 10);
});

test('the corner between the sides of 3 and 4 is a right angle', () => {
  const up = [top[0] - corner[0], top[1] - corner[1]] as const;
  const across = [end[0] - corner[0], end[1] - corner[1]] as const;

  expect(up[0] * across[0] + up[1] * across[1]).toBe(0);
});

test('the triangle sits centred in its 100 by 100 box', () => {
  const xs = pegs.map(([x]) => x);
  const ys = pegs.map(([, y]) => y);

  expect((Math.min(...xs) + Math.max(...xs)) / 2).toBe(50);
  expect((Math.min(...ys) + Math.max(...ys)) / 2).toBe(50);
  expect(cordPath).toBe('M8 18.5 L8 81.5 L92 81.5 Z');
});
