// The days a learner spent time in a lab, which Postgres keeps from their attempts (decision
// record 18), and the streak they make. Days are dates on the learner's own calendar.
import type { Client } from './client.ts';

/** A day the learner spent time in a lab, and how long. */
export interface StudyDay {
  /** Such as 2026-10-14. */
  readonly day: string;
  readonly seconds: number;
}

/** The days in a row the learner studied, and the last of them. */
export interface Streak {
  readonly days: number;
  readonly last: string | null;
}

/** The most rows the Data API returns for one request, as Supabase sets it by default. */
const page = 1000;

/**
 * Every day the learner spent time in a lab, oldest first. A day whose attempts carry no time,
 * such as a pass this browser held from before the learner signed in, isn't one.
 */
export async function readStudyDays(client: Client): Promise<StudyDay[]> {
  const days: StudyDay[] = [];
  for (;;) {
    const { data, error } = await client
      .from('study_days')
      .select('day, seconds')
      .gt('seconds', 0)
      .order('day')
      .range(days.length, days.length + page - 1);
    if (error) throw error;
    days.push(...data);
    if (data.length < page) return days;
  }
}

/**
 * The run of days studied that ends today or, while today has no time in it yet, yesterday, so a
 * streak doesn't end before the day does.
 */
export function streakOf(days: readonly StudyDay[], today: string): Streak {
  const studied = new Set(days.map((each) => each.day));
  const last = studied.has(today) ? today : addDays(today, -1);
  let count = 0;
  while (studied.has(addDays(last, -count))) count++;
  return { days: count, last: count > 0 ? last : null };
}

/** The date `count` days after `day`, or before it when `count` is negative. */
export function addDays(day: string, count: number): string {
  return new Date(Date.parse(`${day}T00:00:00Z`) + count * 86_400_000).toISOString().slice(0, 10);
}

/** The day of the week, from 0 for Monday to 6 for Sunday. */
export function weekdayOf(day: string): number {
  return (new Date(`${day}T00:00:00Z`).getUTCDay() + 6) % 7;
}
