// Dates as the app shows them, in the person's own language and time zone.

const day = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' });

/** Such as "Oct 27, 2026". */
export function dayOf(iso: string): string {
  return day.format(new Date(iso));
}
