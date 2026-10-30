// Dates as the app shows them (decision record 57): in English, as the app is, ordered the way the
// person's English locale orders them, in their time zone. Something that happened in the last 30
// days says how long ago; anything older, and a day such as when someone joined or a link expires,
// says its date, with the year only when it isn't this year.

/** The first English locale the browser names, such as en-GB, so dates read as the person expects. */
export function englishOf(languages: readonly string[]): string {
  return languages.find((tag) => tag === 'en' || tag.startsWith('en-')) ?? 'en';
}

const locale = englishOf(globalThis.navigator?.languages ?? []);
const relative = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });
const thisYear = new Intl.DateTimeFormat(locale, { month: 'short', day: 'numeric' });
const anyYear = new Intl.DateTimeFormat(locale, {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
});
const fullDay = new Intl.DateTimeFormat(locale, {
  weekday: 'short',
  month: 'short',
  day: 'numeric',
  year: 'numeric',
});
const clock = new Intl.DateTimeFormat(locale, {
  hour: 'numeric',
  minute: '2-digit',
  timeZoneName: 'short',
});

const minute = 60_000;
const hour = 60 * minute;
const day = 24 * hour;

/** Such as "Oct 27", or "Oct 27, 2025" in another year. */
export function dayOf(iso: string, now = Date.now()): string {
  const date = new Date(iso);
  return date.getFullYear() === new Date(now).getFullYear()
    ? thisYear.format(date)
    : anyYear.format(date);
}

/** Such as "Tue, Oct 27, 2026 at 9:41 PM GMT+1", which a date shows on hover. */
export function momentOf(iso: string): string {
  const date = new Date(iso);
  return `${fullDay.format(date)} at ${clock.format(date)}`;
}

/**
 * Such as "just now", "5 minutes ago" or "yesterday", and past 30 days the day. A time a moment
 * ahead, as a clock running slow would see one just made, is just now.
 */
export function agoOf(iso: string, now = Date.now()): string {
  const passed = Math.max(0, now - new Date(iso).getTime());
  if (passed < minute) return 'just now';
  if (passed < hour) return relative.format(-Math.floor(passed / minute), 'minute');
  if (passed < day) return relative.format(-Math.floor(passed / hour), 'hour');
  if (passed < 30 * day) return relative.format(-Math.floor(passed / day), 'day');
  return dayOf(iso, now);
}
