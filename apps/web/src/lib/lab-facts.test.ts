import { expect, test } from 'vitest';
import { aboutTime } from './lab-facts';

test('a lab under an hour is given in minutes, and a longer one to the nearest half hour', () => {
  expect(aboutTime(20)).toBe('About 20 minutes');
  expect(aboutTime(60)).toBe('About 1 hour');
  expect(aboutTime(100)).toBe('About 1.5 hours');
  expect(aboutTime(240)).toBe('About 4 hours');
});
