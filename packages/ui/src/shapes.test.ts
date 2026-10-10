import { expect, test } from 'vitest';
import { shapes } from './shapes';

const tags = (markup: string) => [...markup.matchAll(/<(\w+)/g)].map(([, tag]) => tag);

test('there are twelve shapes, each drawn only from lines, circles and paths', () => {
  expect(Object.keys(shapes)).toHaveLength(12);
  for (const markup of Object.values(shapes)) {
    expect(tags(markup).length).toBeGreaterThan(0);
    for (const tag of tags(markup)) expect(['line', 'circle', 'path']).toContain(tag);
  }
});

test("the sun's rays stop well inside the round window, so it reads as a sun, not a wheel", () => {
  const reach = [...shapes.Sun.matchAll(/x2="([\d.-]+)" y2="([\d.-]+)"/g)].map(([, x, y]) =>
    Math.hypot(Number(x) - 48, Number(y) - 48),
  );

  expect(reach).toHaveLength(12);
  for (const r of reach) expect(r).toBeLessThan(40.1);
});

test('the bell curve is tallest in the middle and falls away evenly either side', () => {
  const heights = [...shapes['Bell curve'].matchAll(/M[\d.]+ 82V([\d.]+)/g)].map(
    ([, top]) => 82 - Number(top),
  );

  expect(heights).toHaveLength(13);
  expect(heights).toEqual(heights.toReversed());
  expect(Math.max(...heights)).toBe(heights[6]);
});
