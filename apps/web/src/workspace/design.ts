// A design round's attempt (decision record 42). The clock runs from when the learner starts, as in
// a Problem stage, until they hand in their answers to the follow-up questions. Then the learner
// marks their design against the rubric, each point not met until they mark it met, and passes if
// they meet enough of its points.
import { clockTime } from './problem';

/** What this browser keeps of a Design stage. */
export interface DesignState {
  /** When the learner started this attempt, in milliseconds since 1970, as Date.now() gives it. */
  readonly started: number;
  /** How many times the learner has started, counting this attempt. */
  readonly attempts: number;
  readonly design: string;
  /** Whether the learner has handed in the design, which shows the follow-up questions. */
  readonly handedIn: boolean;
  /** The answer to each follow-up question, in order. */
  readonly answers: readonly string[];
  /** The whole seconds from the start to handing in the answers, or null until they're in. */
  readonly answered: number | null;
  /** Whether each rubric point is met, in order: none until the answers are in. */
  readonly marks: readonly boolean[];
  /** Whether the learner has finished marking, which settles the attempt. */
  readonly marked: boolean;
}

/** An attempt that starts now, keeping the design of the attempt before, if there was one. */
export function startDesign(now: number, before: DesignState | null): DesignState {
  return {
    started: now,
    attempts: (before?.attempts ?? 0) + 1,
    design: before?.design ?? '',
    handedIn: false,
    answers: [],
    answered: null,
    marks: [],
    marked: false,
  };
}

/** The whole seconds from the start to now, or to when the answers were handed in. */
export function designElapsed(state: DesignState, now: number): number {
  return state.answered ?? Math.max(0, Math.floor((now - state.started) / 1000));
}

/** How many of the rubric's points the learner marked as met. */
export function metOf(state: DesignState): number {
  return state.marks.filter((mark) => mark).length;
}

/** What a finished attempt says of the time its answers were handed in. */
export function answeredIn(seconds: number, minutes: number): string {
  const over = seconds - minutes * 60;
  return over > 0
    ? `Handed in at ${clockTime(seconds)}, ${clockTime(over)} over its ${minutes} minutes.`
    : `Handed in at ${clockTime(seconds)}, inside its ${minutes} minutes.`;
}

const isWhole = (value: unknown, least: number) =>
  Number.isInteger(value) && (value as number) >= least;

/** A kept state, or null if there is none or it can't be read. */
export function designOf(text: string | null): DesignState | null {
  if (text === null) return null;
  try {
    const state = JSON.parse(text) as Partial<DesignState>;
    const valid =
      Number.isFinite(state.started) &&
      isWhole(state.attempts, 1) &&
      typeof state.design === 'string' &&
      typeof state.handedIn === 'boolean' &&
      Array.isArray(state.answers) &&
      state.answers.every((answer) => typeof answer === 'string') &&
      (state.answered === null || isWhole(state.answered, 0)) &&
      Array.isArray(state.marks) &&
      state.marks.every((mark) => typeof mark === 'boolean') &&
      typeof state.marked === 'boolean';
    return valid ? (state as DesignState) : null;
  } catch {
    return null;
  }
}
