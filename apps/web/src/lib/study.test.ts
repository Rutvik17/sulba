import { addDays, type StudyDay, streakOf } from '@sulba/data/study';
import { describe, expect, it } from 'vitest';
import { calendarOf, dateOf, durationOf } from './study';

const today = '2026-10-14';

function calendar(days: StudyDay[]) {
  return calendarOf(days, streakOf(days, today), today);
}

describe('calendarOf', () => {
  it('shows twelve weeks up to today, in columns from Monday', () => {
    const { weeks, span, studied } = calendar([]);
    expect(span).toBe(84);
    expect(studied).toEqual([]);
    // 23 July 2026 is a Thursday, so the first column starts with three empty days.
    expect(weeks).toHaveLength(13);
    expect(weeks[0]?.slice(0, 4).map((cell) => cell?.day ?? null)).toEqual([
      null,
      null,
      null,
      '2026-07-23',
    ]);
    expect(weeks.at(-1)?.map((cell) => cell?.day)).toEqual([
      '2026-10-12',
      '2026-10-13',
      '2026-10-14',
    ]);
    expect(weeks.flat().filter((cell) => cell?.today)).toEqual([
      expect.objectContaining({ day: today, label: 'Wednesday 14 October 2026: not studied' }),
    ]);
  });

  it('marks the streak apart from the other days studied', () => {
    const days = [
      { day: '2026-10-01', seconds: 1500 },
      { day: '2026-10-12', seconds: 600 },
      { day: '2026-10-13', seconds: 3900 },
    ];
    const { studied } = calendar(days);
    expect(studied.map(({ day, inStreak, label }) => ({ day, inStreak, label }))).toEqual([
      { day: '2026-10-01', inStreak: false, label: 'Thursday 1 October 2026: 25 minutes' },
      { day: '2026-10-12', inStreak: true, label: 'Monday 12 October 2026: 10 minutes' },
      { day: '2026-10-13', inStreak: true, label: 'Tuesday 13 October 2026: 1 hour 5 minutes' },
    ]);
  });

  it('grows to show the whole of a longer streak', () => {
    const days = Array.from({ length: 100 }, (_, n) => ({
      day: addDays('2026-10-13', -n),
      seconds: 300,
    }));
    const { span, studied } = calendar(days);
    expect(span).toBe(101);
    expect(studied).toHaveLength(100);
    expect(studied.every((cell) => cell.inStreak)).toBe(true);
  });

  it('names each month over the week it starts in', () => {
    expect(calendar([]).months).toEqual([
      { week: 1, name: 'Aug' },
      { week: 6, name: 'Sep' },
      { week: 10, name: 'Oct' },
    ]);
    const later = calendarOf([], { days: 0, last: null }, '2026-11-25');
    expect(later.months[0]).toEqual({ week: 0, name: 'Sep' });
  });
});

describe('dateOf', () => {
  it('writes the date out in full', () => {
    expect(dateOf('2026-10-14')).toBe('Wednesday 14 October 2026');
    expect(dateOf('2027-01-03')).toBe('Sunday 3 January 2027');
  });
});

describe('durationOf', () => {
  it('rounds to the minute, in hours and minutes', () => {
    expect(durationOf(29)).toBe('less than a minute');
    expect(durationOf(60)).toBe('1 minute');
    expect(durationOf(90)).toBe('2 minutes');
    expect(durationOf(3600)).toBe('1 hour');
    expect(durationOf(3590)).toBe('1 hour');
    expect(durationOf(7260)).toBe('2 hours 1 minute');
  });
});
