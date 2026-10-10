import { expect, test } from 'vitest';
import { cordPath, knots, loop, pegs, sides } from './mark';

type Point = (typeof pegs)[number];

const [top, corner, end] = pegs;
const distance = (a: Point, b: Point) => Math.hypot(b[0] - a[0], b[1] - a[1]);
const unit = distance(top, corner) / sides[0];

test('the sides are 3, 4 and 5, so the squares on the first two add up to the third', () => {
  const [up, across, back] = sides;

  expect(up ** 2 + across ** 2).toBe(back ** 2);
});

test('the cord makes sides in the ratio 3 : 4 : 5', () => {
  expect(distance(corner, end) / unit).toBeCloseTo(sides[1], 10);
  expect(distance(end, top) / unit).toBeCloseTo(sides[2], 10);
});

test('the corner between the sides of 3 and 4 is a right angle', () => {
  const up = [top[0] - corner[0], top[1] - corner[1]] as const;
  const across = [end[0] - corner[0], end[1] - corner[1]] as const;

  expect(up[0] * across[0] + up[1] * across[1]).toBe(0);
});

test('the pegs and knots split the cord into 12 equal lengths', () => {
  const lengths = loop.map((point, i) => distance(point, loop[(i + 1) % loop.length] ?? point));

  expect(loop).toHaveLength(12);
  for (const length of lengths) expect(length / unit).toBeCloseTo(1, 10);
  expect(knots).toHaveLength(12 - pegs.length);
});

test('the triangle sits centred in its 100 by 100 box', () => {
  const xs = pegs.map(([x]) => x);
  const ys = pegs.map(([, y]) => y);

  expect((Math.min(...xs) + Math.max(...xs)) / 2).toBe(50);
  expect((Math.min(...ys) + Math.max(...ys)) / 2).toBe(50);
  expect(cordPath).toBe('M8 18.5 L8 81.5 L92 81.5 Z');
});
