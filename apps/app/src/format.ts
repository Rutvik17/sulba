// Dates as the app shows them, in the person's own language and time zone.

const day = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
const moment = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' });
const relative = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' });

/** Such as "Oct 27, 2026". */
export function dayOf(iso: string): string {
  return day.format(new Date(iso));
}

/** Such as "Oct 27, 2026, 9:41 PM", for the title a relative time shows on hover. */
export function momentOf(iso: string): string {
  return moment.format(new Date(iso));
}

const minute = 60_000;
const hour = 60 * minute;
const days = 24 * hour;

/** How long ago, such as "5 minutes ago" or "yesterday", and past four weeks the day itself. */
export function ago(iso: string, now = Date.now()): string {
  const passed = Math.max(0, now - new Date(iso).getTime());
  if (passed < minute) return 'just now';
  if (passed < hour) return relative.format(-Math.floor(passed / minute), 'minute');
  if (passed < days) return relative.format(-Math.floor(passed / hour), 'hour');
  if (passed < 28 * days) return relative.format(-Math.floor(passed / days), 'day');
  return dayOf(iso);
}
