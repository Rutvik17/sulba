import { expect, test } from 'vitest';
import { clock, clockTime, elapsed, problemOf, solvedIn } from './problem';

test('the clock shows minutes and seconds, and hours once past an hour', () => {
  expect(clockTime(0)).toBe('0:00');
  expect(clockTime(65)).toBe('1:05');
  expect(clockTime(1200)).toBe('20:00');
  expect(clockTime(3730)).toBe('1:02:10');
  expect(clockTime(59.9)).toBe('0:59');
  expect(clock(751, 20)).toBe('12:31 of 20:00');
});

test('a solved problem says whether it took longer than its minutes', () => {
  expect(solvedIn(872, 20)).toBe('Solved in 14:32, inside its 20 minutes.');
  expect(solvedIn(1200, 20)).toBe('Solved in 20:00, inside its 20 minutes.');
  expect(solvedIn(1450, 20)).toBe('Solved in 24:10, 4:10 over its 20 minutes.');
});

test('the time runs from the start until the problem is solved', () => {
  const started = { started: 1_000_000, plan: 'A set of what I have seen.', coding: true };
  expect(elapsed({ ...started, solved: null }, 1_000_000 + 61_500)).toBe(61);
  expect(elapsed({ ...started, solved: 300 }, 1_000_000 + 900_000)).toBe(300);
  expect(elapsed({ ...started, solved: null }, 999_000)).toBe(0);
});

test('a kept state is read back, and one that is missing or broken is none', () => {
  const state = {
    started: 1_000_000,
    plan: 'Sort, then two pointers.',
    coding: false,
    solved: null,
  };
  expect(problemOf(JSON.stringify(state))).toEqual(state);
  expect(problemOf(JSON.stringify({ ...state, solved: 42 }))).toEqual({ ...state, solved: 42 });
  expect(problemOf(null)).toBeNull();
  expect(problemOf('{')).toBeNull();
  expect(problemOf(JSON.stringify({ ...state, plan: 7 }))).toBeNull();
  expect(problemOf(JSON.stringify({ ...state, solved: -1 }))).toBeNull();
});
