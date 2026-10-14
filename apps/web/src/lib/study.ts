// The account page's calendar of days studied: a column a week from Monday, so a streak reads as a
// run of marked days that ends today or yesterday.
import { addDays, type Streak, type StudyDay, weekdayOf } from '@sulba/data/study';

/** The calendar shows twelve weeks, or more when the streak is longer. */
const shortest = 84;

const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const months = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

export interface CalendarDay {
  readonly day: string;
  readonly seconds: number;
  readonly inStreak: boolean;
  readonly today: boolean;
  /** Such as "Wednesday 14 October 2026: 25 minutes". */
  readonly label: string;
}

export interface Calendar {
  /** A column a week, Monday first; the days before the calendar starts are null. */
  readonly weeks: readonly (readonly (CalendarDay | null)[])[];
  /** A month's short name over the week it starts in. */
  readonly months: readonly { readonly week: number; readonly name: string }[];
  /** How many days the calendar shows, up to today. */
  readonly span: number;
  /** The days studied among them, oldest first. */
  readonly studied: readonly CalendarDay[];
}

export function calendarOf(days: readonly StudyDay[], streak: Streak, today: string): Calendar {
  const seconds = new Map(days.map((each) => [each.day, each.seconds]));
  const last = streak.last ?? today;
  const first = addDays(last, 1 - streak.days);
  const span = Math.max(shortest, streak.days + (last === today ? 0 : 1));
  const start = addDays(today, 1 - span);
  const cells: (CalendarDay | null)[] = Array.from({ length: weekdayOf(start) }, () => null);
  for (let n = 0; n < span; n++) {
    const day = addDays(start, n);
    const time = seconds.get(day) ?? 0;
    cells.push({
      day,
      seconds: time,
      inStreak: time > 0 && day >= first && day <= last,
      today: day === today,
      label: `${dateOf(day)}: ${time > 0 ? durationOf(time) : 'not studied'}`,
    });
  }
  const weeks = Array.from({ length: Math.ceil(cells.length / 7) }, (_, week) =>
    cells.slice(week * 7, week * 7 + 7),
  );
  return {
    weeks,
    months: monthsOf(weeks),
    span,
    studied: cells.filter((cell): cell is CalendarDay => cell !== null && cell.seconds > 0),
  };
}

/** Such as "Wednesday 14 October 2026". */
export function dateOf(day: string): string {
  const weekday = weekdays[weekdayOf(day)] ?? '';
  const month = months[Number(day.slice(5, 7)) - 1] ?? '';
  return `${weekday} ${Number(day.slice(8))} ${month} ${day.slice(0, 4)}`;
}

/** Such as "less than a minute", "25 minutes" or "1 hour 5 minutes". */
export function durationOf(seconds: number): string {
  const minutes = Math.round(seconds / 60);
  if (minutes === 0) return 'less than a minute';
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  const parts = [
    ...(hours > 0 ? [`${hours} ${hours === 1 ? 'hour' : 'hours'}`] : []),
    ...(rest > 0 ? [`${rest} ${rest === 1 ? 'minute' : 'minutes'}`] : []),
  ];
  return parts.join(' ');
}

/**
 * Each month goes over the week its first day is in. The first week takes the month it shows
 * when no other name would sit too close to it.
 */
function monthsOf(weeks: readonly (readonly (CalendarDay | null)[])[]) {
  const named = weeks.flatMap((days, week) => {
    const first = days.find((each) => each?.day.endsWith('-01'));
    return first ? [{ week, name: shortMonth(first.day) }] : [];
  });
  const opening = weeks[0]?.find((each) => each !== null);
  const roomy = (named[0]?.week ?? Number.POSITIVE_INFINITY) >= 2;
  return opening && named[0]?.week !== 0 && roomy
    ? [{ week: 0, name: shortMonth(opening.day) }, ...named]
    : named;
}

function shortMonth(day: string): string {
  return (months[Number(day.slice(5, 7)) - 1] ?? '').slice(0, 3);
}
