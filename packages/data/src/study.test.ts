import { describe, expect, it } from 'vitest';
import type { Client } from './client.ts';
import { addDays, readStudyDays, type StudyDay, streakOf, weekdayOf } from './study.ts';

const studied = (...days: string[]): StudyDay[] => days.map((day) => ({ day, seconds: 600 }));

describe('streakOf', () => {
  it('counts the days in a row up to today', () => {
    const days = studied('2026-10-09', '2026-10-12', '2026-10-13', '2026-10-14');
    expect(streakOf(days, '2026-10-14')).toEqual({ days: 3, last: '2026-10-14' });
  });

  it('keeps a streak that ends yesterday until today is over', () => {
    const days = studied('2026-10-12', '2026-10-13');
    expect(streakOf(days, '2026-10-14')).toEqual({ days: 2, last: '2026-10-13' });
  });

  it('has no streak when neither today nor yesterday was studied', () => {
    expect(streakOf(studied('2026-10-11', '2026-10-12'), '2026-10-14')).toEqual({
      days: 0,
      last: null,
    });
    expect(streakOf([], '2026-10-14')).toEqual({ days: 0, last: null });
  });

  it('runs across months and years, and ignores the order days come in', () => {
    const days = studied('2027-01-01', '2026-12-31', '2026-12-30');
    expect(streakOf(days, '2027-01-01')).toEqual({ days: 3, last: '2027-01-01' });
  });
});

describe('days', () => {
  it('adds and subtracts days across months, years and clock changes', () => {
    expect(addDays('2026-10-14', 1)).toBe('2026-10-15');
    expect(addDays('2026-03-01', -1)).toBe('2026-02-28');
    expect(addDays('2028-03-01', -1)).toBe('2028-02-29');
    expect(addDays('2026-12-31', 1)).toBe('2027-01-01');
    expect(addDays('2026-10-25', 1)).toBe('2026-10-26');
  });

  it('names the weekday from Monday', () => {
    expect(weekdayOf('2026-10-12')).toBe(0);
    expect(weekdayOf('2026-10-14')).toBe(2);
    expect(weekdayOf('2026-10-18')).toBe(6);
  });
});

describe('readStudyDays', () => {
  /** A client whose study_days rows are `rows`, served a page at a time as the Data API does. */
  function client(rows: StudyDay[]) {
    const requests: { seconds: number; from: number; to: number }[] = [];
    const query = (seconds: number) => ({
      order: () => ({
        range: async (from: number, to: number) => {
          requests.push({ seconds, from, to });
          return { data: rows.slice(from, Math.min(to + 1, from + 1000)), error: null };
        },
      }),
    });
    const fake = {
      from: () => ({ select: () => ({ gt: (_: string, value: number) => query(value) }) }),
    };
    return { client: fake as unknown as Client, requests };
  }

  it('reads every day with time in it, a page at a time', async () => {
    const rows = Array.from({ length: 1500 }, (_, n) => ({
      day: addDays('2022-01-01', n),
      seconds: 60,
    }));
    const { client: fake, requests } = client(rows);
    expect(await readStudyDays(fake)).toEqual(rows);
    expect(requests).toEqual([
      { seconds: 0, from: 0, to: 999 },
      { seconds: 0, from: 1000, to: 1999 },
    ]);
  });
});
