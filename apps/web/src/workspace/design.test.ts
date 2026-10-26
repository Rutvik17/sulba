import { expect, test } from 'vitest';
import {
  answeredIn,
  type DesignState,
  designElapsed,
  designOf,
  metOf,
  startDesign,
} from './design';

const handedIn: DesignState = {
  started: 1_000_000,
  attempts: 1,
  design: 'One service, one table of ballots.',
  handedIn: true,
  answers: ['The count keeps the ids it has seen.', 'The table, then the service.'],
  answered: 1500,
  marks: [true, false, false],
  marked: false,
};

test('an attempt starts with an empty design, and a new one keeps the design before it', () => {
  expect(startDesign(5000, null)).toEqual({
    started: 5000,
    attempts: 1,
    design: '',
    handedIn: false,
    answers: [],
    answered: null,
    marks: [],
    marked: false,
  });
  expect(startDesign(9000, { ...handedIn, marked: true })).toEqual({
    started: 9000,
    attempts: 2,
    design: 'One service, one table of ballots.',
    handedIn: false,
    answers: [],
    answered: null,
    marks: [],
    marked: false,
  });
});

test('the time runs from the start until the answers are handed in', () => {
  const writing = startDesign(1_000_000, null);
  expect(designElapsed(writing, 1_000_000 + 61_500)).toBe(61);
  expect(designElapsed(writing, 999_000)).toBe(0);
  expect(designElapsed(handedIn, 1_000_000 + 3_600_000)).toBe(1500);
});

test('the marks count the points met', () => {
  expect(metOf(handedIn)).toBe(1);
  expect(metOf({ ...handedIn, marks: [true, true, true] })).toBe(3);
  expect(metOf(startDesign(5000, null))).toBe(0);
});

test('a finished attempt says whether its answers came in inside its minutes', () => {
  expect(answeredIn(1500, 30)).toBe('Handed in at 25:00, inside its 30 minutes.');
  expect(answeredIn(1800, 30)).toBe('Handed in at 30:00, inside its 30 minutes.');
  expect(answeredIn(1930, 30)).toBe('Handed in at 32:10, 2:10 over its 30 minutes.');
});

test('a kept state is read back, and one that is missing or broken is none', () => {
  expect(designOf(JSON.stringify(handedIn))).toEqual(handedIn);
  expect(designOf(JSON.stringify(startDesign(5000, null)))).toEqual(startDesign(5000, null));
  expect(designOf(null)).toBeNull();
  expect(designOf('{')).toBeNull();
  expect(designOf(JSON.stringify({ ...handedIn, attempts: 0 }))).toBeNull();
  expect(designOf(JSON.stringify({ ...handedIn, answers: [7] }))).toBeNull();
  expect(designOf(JSON.stringify({ ...handedIn, answered: -1 }))).toBeNull();
  expect(designOf(JSON.stringify({ ...handedIn, marks: [null] }))).toBeNull();
});
