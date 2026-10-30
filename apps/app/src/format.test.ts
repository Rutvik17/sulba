import { describe, expect, test } from 'vitest';
import { agoOf, dayOf, englishOf, momentOf } from './format';

const now = Date.parse('2026-10-27T12:00:00Z');

describe('agoOf', () => {
  test('says how long ago something within 30 days happened', () => {
    expect(agoOf('2026-10-27T11:59:30Z', now)).toBe('just now');
    expect(agoOf('2026-10-27T11:59:00Z', now)).toBe('1 minute ago');
    expect(agoOf('2026-10-27T11:55:00Z', now)).toBe('5 minutes ago');
    expect(agoOf('2026-10-27T09:00:00Z', now)).toBe('3 hours ago');
    expect(agoOf('2026-10-26T11:00:00Z', now)).toBe('yesterday');
    expect(agoOf('2026-10-21T12:00:00Z', now)).toBe('6 days ago');
    expect(agoOf('2026-09-28T11:59:59Z', now)).toBe('29 days ago');
  });

  test('gives the day of anything older', () => {
    expect(agoOf('2026-09-27T12:00:00Z', now)).toBe('Sep 27');
    expect(agoOf('2025-12-24T12:00:00Z', now)).toBe('Dec 24, 2025');
  });

  test('takes a time a moment ahead as just now', () => {
    expect(agoOf('2026-10-27T12:00:20Z', now)).toBe('just now');
  });
});

describe('dayOf', () => {
  test('gives the year only when it isn’t this year', () => {
    expect(dayOf('2026-10-20T09:00:00Z', now)).toBe('Oct 20');
    expect(dayOf('2025-10-20T09:00:00Z', now)).toBe('Oct 20, 2025');
  });
});

describe('momentOf', () => {
  test('gives the weekday, the day, the time and the time zone', () => {
    // In the time zone of the machine that runs the tests, where midday UTC is still Oct 27.
    expect(momentOf('2026-10-27T12:41:00Z')).toMatch(/^Tue, Oct 27, 2026 at \d{1,2}:41 [AP]M \S+$/);
  });
});

describe('englishOf', () => {
  test('takes the first English locale the browser names, or plain English', () => {
    expect(englishOf(['de-DE', 'en-GB', 'en-US'])).toBe('en-GB');
    expect(englishOf(['en'])).toBe('en');
    expect(englishOf(['fr-FR'])).toBe('en');
    expect(englishOf([])).toBe('en');
  });
});
