import { useSyncExternalStore } from 'react';
import { agoOf, dayOf, momentOf } from './format';

// One clock for every time on the page, which ticks each 30 seconds while something shows one, so
// "just now" becomes "1 minute ago" without a reload.
const listeners = new Set<() => void>();
let now = Date.now();
let ticking: ReturnType<typeof setInterval> | undefined;

function subscribe(listener: () => void) {
  listeners.add(listener);
  if (!ticking) {
    now = Date.now();
    ticking = setInterval(() => {
      now = Date.now();
      for (const each of listeners) each();
    }, 30_000);
  }
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0) {
      clearInterval(ticking);
      ticking = undefined;
    }
  };
}

/**
 * A time as the app shows it (decision record 57): how long ago, or the day, with the full date and
 * time on hover.
 */
export function When({ at, day = false }: { at: string; day?: boolean }) {
  const current = useSyncExternalStore(subscribe, () => now);
  return (
    <time dateTime={at} title={momentOf(at)}>
      {day ? dayOf(at, current) : agoOf(at, current)}
    </time>
  );
}
