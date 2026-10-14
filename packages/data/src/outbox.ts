// Attempts wait in local storage until Supabase has them, so a reload or a day offline loses none.
// Each carries an id made here, so a batch sent twice adds nothing (decision record 18).

/** What happened in a stage. */
export type Event =
  | { readonly kind: 'run'; readonly tests: Count; readonly checks: Count | null }
  | { readonly kind: 'hint'; readonly hint: number }
  | { readonly kind: 'solution' }
  | { readonly kind: 'pass'; readonly review: Review | null };

/** How many of some tests or checks passed. */
export interface Count {
  readonly passed: number;
  readonly total: number;
}

/** A finished Catch review: the checks of the problems caught, and how many problems it has. */
export interface Review {
  readonly caught: readonly string[];
  readonly problems: number;
}

/** An attempt as the attempts table takes it. The database fills in the learner and arrival. */
export interface Attempt {
  readonly id: string;
  readonly stage_id: string;
  readonly stage_version: string;
  readonly kind: Event['kind'];
  readonly tests_passed: number | null;
  readonly tests_total: number | null;
  readonly checks_passed: number | null;
  readonly checks_total: number | null;
  readonly hint: number | null;
  readonly caught: string[] | null;
  readonly problems: number | null;
  readonly seconds: number;
  readonly happened_at: string;
  readonly day: string;
}

/** The longest time one attempt can carry, as the attempts table allows. */
export const maxSeconds = 3600;

/** The calendar day of a moment where the learner is, such as 2026-10-14. */
export function localDay(at: Date): string {
  const month = String(at.getMonth() + 1).padStart(2, '0');
  const day = String(at.getDate()).padStart(2, '0');
  return `${at.getFullYear()}-${month}-${day}`;
}

export function attemptOf(
  stage: { readonly id: string; readonly version: string },
  event: Event,
  seconds: number,
  at: Date,
  id: string = crypto.randomUUID(),
): Attempt {
  return {
    id,
    stage_id: stage.id,
    stage_version: stage.version,
    kind: event.kind,
    tests_passed: event.kind === 'run' ? event.tests.passed : null,
    tests_total: event.kind === 'run' ? event.tests.total : null,
    checks_passed: event.kind === 'run' ? (event.checks?.passed ?? null) : null,
    checks_total: event.kind === 'run' ? (event.checks?.total ?? null) : null,
    hint: event.kind === 'hint' ? event.hint : null,
    caught: event.kind === 'pass' && event.review ? [...event.review.caught] : null,
    problems: event.kind === 'pass' && event.review ? event.review.problems : null,
    seconds: Math.min(maxSeconds, Math.max(0, Math.round(seconds))),
    happened_at: at.toISOString(),
    day: localDay(at),
  };
}

const outboxKey = 'sulba:outbox';

/** The most attempts kept unsent, about a month of heavy study; past it the oldest go first. */
const capacity = 5000;

type Storage = Pick<globalThis.Storage, 'getItem' | 'setItem' | 'removeItem'>;

/** The attempts not yet sent, oldest first. */
export class Outbox {
  readonly #storage: Storage;

  constructor(storage: Storage) {
    this.#storage = storage;
  }

  all(): Attempt[] {
    try {
      const kept: unknown = JSON.parse(this.#storage.getItem(outboxKey) ?? '[]');
      return Array.isArray(kept) ? kept.filter(isAttempt) : [];
    } catch {
      return [];
    }
  }

  add(attempt: Attempt): void {
    this.#save([...this.all(), attempt].slice(-capacity));
  }

  /** Takes out the attempts Supabase has, or will never take. */
  remove(ids: ReadonlySet<string>): void {
    this.#save(this.all().filter((attempt) => !ids.has(attempt.id)));
  }

  /** Empties it, at sign-out, so no attempt goes to whichever account signs in next. */
  clear(): void {
    this.#save([]);
  }

  #save(attempts: readonly Attempt[]): void {
    try {
      if (attempts.length === 0) this.#storage.removeItem(outboxKey);
      else this.#storage.setItem(outboxKey, JSON.stringify(attempts));
    } catch {
      // Storage is blocked or full: these attempts last only as long as the page.
    }
  }
}

const kinds: ReadonlySet<unknown> = new Set(['run', 'hint', 'solution', 'pass']);

function isAttempt(value: unknown): value is Attempt {
  if (typeof value !== 'object' || value === null) return false;
  const attempt = value as Record<keyof Attempt, unknown>;
  return (
    typeof attempt.id === 'string' &&
    typeof attempt.stage_id === 'string' &&
    typeof attempt.stage_version === 'string' &&
    kinds.has(attempt.kind) &&
    typeof attempt.seconds === 'number' &&
    typeof attempt.happened_at === 'string' &&
    typeof attempt.day === 'string'
  );
}
