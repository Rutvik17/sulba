// An interview problem's time and plan. The clock runs from when the learner starts it, as an
// interviewer's does from when they give the problem, and the plan comes before the code.

/** What this browser keeps of a Problem stage. */
export interface ProblemState {
  /** When the learner started, in milliseconds since 1970, as Date.now() gives it. */
  readonly started: number;
  readonly plan: string;
  /** Whether the learner has finished the plan, which opens the code. */
  readonly coding: boolean;
  /** The whole seconds from the start to the first pass, or null until it passes. */
  readonly solved: number | null;
}

/** A time on the clock: "4:05", "20:00", or past an hour "1:02:10". */
export function clockTime(seconds: number): string {
  const whole = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(whole / 3600);
  const minutes = Math.floor((whole % 3600) / 60);
  const rest = String(whole % 60).padStart(2, '0');
  return hours > 0 ? `${hours}:${String(minutes).padStart(2, '0')}:${rest}` : `${minutes}:${rest}`;
}

/** The clock as it reads while the problem is open: "12:31 of 20:00". */
export function clock(seconds: number, minutes: number): string {
  return `${clockTime(seconds)} of ${clockTime(minutes * 60)}`;
}

/** What a solved problem says of its time. */
export function solvedIn(seconds: number, minutes: number): string {
  const over = seconds - minutes * 60;
  return over > 0
    ? `Solved in ${clockTime(seconds)}, ${clockTime(over)} over its ${minutes} minutes.`
    : `Solved in ${clockTime(seconds)}, inside its ${minutes} minutes.`;
}

/** The whole seconds from the start to now. */
export function elapsed(state: ProblemState, now: number): number {
  return state.solved ?? Math.max(0, Math.floor((now - state.started) / 1000));
}

/** A kept state, or null if there is none or it can't be read. */
export function problemOf(text: string | null): ProblemState | null {
  if (text === null) return null;
  try {
    const { started, plan, coding, solved } = JSON.parse(text) as Partial<ProblemState>;
    const valid =
      Number.isFinite(started) &&
      typeof plan === 'string' &&
      typeof coding === 'boolean' &&
      (solved === null || (Number.isInteger(solved) && (solved as number) >= 0));
    return valid ? { started: started as number, plan, coding, solved: solved ?? null } : null;
  } catch {
    return null;
  }
}
