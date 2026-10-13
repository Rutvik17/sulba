import { expect, test } from 'vitest';
import { decimalsOf, labelEvery, pathOf, ticksOf } from './plot';

test('a tick is written with as many decimals as the step has', () => {
  expect(decimalsOf(2)).toBe(0);
  expect(decimalsOf(20)).toBe(0);
  expect(decimalsOf(0.25)).toBe(2);
  expect(decimalsOf(1e-7)).toBe(7);
  expect(decimalsOf(2.5e-7)).toBe(8);
  expect(ticksOf({ min: 0, max: 1, step: 0.25, label: 'p' }).map(({ label }) => label)).toEqual([
    '0.00',
    '0.25',
    '0.50',
    '0.75',
    '1.00',
  ]);
});

test('ticks land on whole steps, and none reads -0', () => {
  const ticks = ticksOf({ min: -0.3, max: 0.3, step: 0.1, label: 'b' });
  expect(ticks.map(({ value }) => value)).toEqual([-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3]);
  expect(ticks.map(({ label }) => label)).toContain('0.0');
});

test('labels skip ticks when they would crowd each other', () => {
  expect(labelEvery(60, 40)).toBe(1);
  expect(labelEvery(30, 40)).toBe(2);
  expect(labelEvery(12, 40)).toBe(4);
});

test('a line breaks where a value is missing or not finite', () => {
  const place = (x: number, y: number) => [x * 10, 100 - y * 10] as const;
  expect(pathOf([0, 1, 2, 3, 4], [1, 2, null, 4, Number.NaN], place)).toBe('M0 90L10 80M30 60');
});

test('a value far off the chart is drawn at a distance SVG can handle', () => {
  const place = (x: number, y: number) => [x, -y] as const;
  expect(pathOf([0, 1], [0, 1e300], place)).toBe('M0 0L1 -1000000');
});
