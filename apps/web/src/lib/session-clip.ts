// Fig. 1 on the landing: an assistant's standardize() fails two of four tests, the learner adds
// axis=0 to the mean and the standard deviation, and all four pass. Every frame is a function of
// one clock, so the player can pause, hold the last frame for reduced motion, and be tested.

/** The test's matrix: two columns with different means. */
export const matrix: readonly (readonly number[])[] = [
  [1, 10],
  [2, 20],
  [3, 30],
];

const mean = (values: readonly number[]) => values.reduce((sum, v) => sum + v, 0) / values.length;
const std = (values: readonly number[]) => {
  const m = mean(values);
  return Math.sqrt(mean(values.map((v) => (v - m) ** 2)));
};
const columns = (x: readonly (readonly number[])[]) =>
  (x[0] ?? []).map((_, j) => x.map((row) => row[j] ?? Number.NaN));

/** The assistant's draft: one mean and one standard deviation for the whole matrix. */
export function draftStandardize(x: readonly (readonly number[])[]): number[][] {
  const all = x.flat();
  const m = mean(all);
  const s = std(all);
  return x.map((row) => row.map((v) => (v - m) / s));
}

/** The fix, axis=0: each column scaled by its own mean and standard deviation. */
export function fixedStandardize(x: readonly (readonly number[])[]): number[][] {
  const stats = columns(x).map((column) => [mean(column), std(column)] as const);
  return x.map((row) =>
    row.map((v, j) => {
      const [m, s] = stats[j] ?? [Number.NaN, Number.NaN];
      return (v - m) / s;
    }),
  );
}

export const columnMeans = (x: readonly (readonly number[])[]) => columns(x).map(mean);
export const columnStds = (x: readonly (readonly number[])[]) => columns(x).map(std);

const list = (values: readonly number[]) =>
  `[${values.map((v) => (Object.is(Math.round(v * 100) / 100, -0) ? 0 : v).toFixed(2)).join(', ')}]`;

/** The failing test's input and message, as the clip shows them, so the numbers trace back to X. */
export const failure = {
  input: `X = [${matrix.map((row) => `[${row.join(', ')}]`).join(', ')}]`,
  message: `Column means are ${list(columnMeans(draftStandardize(matrix)))}, expected [0, 0]`,
};

export const LOOP = 11_000;
export const FIX = 'axis=0';
const CHAR = 75;

// Milliseconds from the start of the loop.
export const at = {
  press1: 1500,
  results1: 1700,
  failed: 2560,
  typeA: 3950,
  typeB: 5250,
  press2: 6500,
  results2: 6700,
  passed: 7400,
  done: 7700,
  fadeOut: 10_200,
  reset: 10_500,
  fadeIn: 10_560,
} as const;

/** Where the pointer can be: at rest, on Run tests, or in the code where an edit starts or ends. */
export type Place = 'rest' | 'run' | 'a' | 'b' | 'a-end' | 'b-end';
export type TestState = 'idle' | 'running' | 'pass' | 'fail';
export type Summary = 'idle' | 'running' | 'fail' | 'pass';

const firstRun: readonly TestState[] = ['pass', 'fail', 'fail', 'pass'];

// The pointer's journey in straight lines: [start, end, from, to]. After typing it comes back
// where the typing ended, as if the hand had followed the caret.
const moves: readonly (readonly [number, number, Place, Place])[] = [
  [600, 1450, 'rest', 'run'],
  [3000, 3800, 'run', 'a'],
  [4550, 5100, 'a-end', 'b'],
  [5800, 6450, 'b-end', 'run'],
  [7700, 8600, 'run', 'rest'],
];

const presses: readonly (readonly [number, number])[] = [
  [at.press1, at.press1 + 120],
  [3800, 3900],
  [5100, 5200],
  [at.press2, at.press2 + 120],
];

export const summaries: Record<Summary, string> = {
  idle: 'Not run yet',
  running: 'Running…',
  fail: '2 failed · 2 passed',
  pass: '4 passed',
};

export interface Frame {
  typedA: number;
  typedB: number;
  freshA: boolean;
  freshB: boolean;
  caret: 'a' | 'b' | null;
  typing: boolean;
  blink: boolean;
  /** As on macOS and Windows, the pointer hides while you type and returns when it moves. */
  away: boolean;
  tests: TestState[];
  summary: Summary;
  failNote: boolean;
  done: boolean;
  /** The Run tests button is held down. */
  down: boolean;
  /** The pointer is clicking. */
  press: boolean;
  /** Between loops, the stage fades out and back in. */
  hidden: boolean;
  pointer: { from: Place; to: Place; k: number };
}

const ease = (x: number) => (x < 0.5 ? 4 * x ** 3 : 1 - (-2 * x + 2) ** 3 / 2);

function pointerAt(t: number): Frame['pointer'] {
  let place: Frame['pointer'] = { from: 'rest', to: 'rest', k: 1 };
  for (const [start, end, from, to] of moves) {
    if (t < start) break;
    place = { from, to, k: t >= end ? 1 : ease((t - start) / (end - start)) };
  }
  return place;
}

const awayUntil = (start: number) => moves.find(([moveStart]) => moveStart > start)?.[0] ?? start;

export function frameAt(clock: number): Frame {
  const t = clock >= at.reset ? -1 : clock;
  const typed = (start: number) =>
    t < start ? 0 : Math.min(FIX.length, Math.floor((t - start) / CHAR) + 1);
  const second = t >= at.press2 + 120;
  const typingFrom = (start: number) => t >= start && t < start + FIX.length * CHAR;

  return {
    typedA: typed(at.typeA),
    typedB: typed(at.typeB),
    freshA: t >= at.typeA && t < at.typeA + 1600,
    freshB: t >= at.typeB && t < at.typeB + 1600,
    caret: t >= 3850 && t < 4800 ? 'a' : t >= 5150 && t < 6100 ? 'b' : null,
    typing: typingFrom(at.typeA) || typingFrom(at.typeB),
    blink: Math.floor(t / 530) % 2 === 0,
    away: (t >= at.typeA && t < awayUntil(at.typeA)) || (t >= at.typeB && t < awayUntil(at.typeB)),
    tests: firstRun.map((first, i) => {
      if (second) {
        const start = at.results2 + i * 180;
        return t < start ? 'idle' : t < start + 160 ? 'running' : 'pass';
      }
      const start = at.results1 + i * 220;
      return t < start ? 'idle' : t < start + 200 ? 'running' : first;
    }),
    summary: second
      ? t >= at.passed
        ? 'pass'
        : 'running'
      : t >= at.failed
        ? 'fail'
        : t >= at.press1 + 120
          ? 'running'
          : 'idle',
    failNote: t >= at.failed + 40 && !second,
    done: t >= at.done,
    down: [at.press1, at.press2].some((press) => t >= press && t < press + 120),
    press: presses.some(([start, end]) => t >= start && t < end),
    hidden: clock >= at.fadeOut && clock < at.fadeIn,
    pointer: pointerAt(t),
  };
}

/** The moment reduced motion shows: the session finished, all four tests passed. */
export const finished = 9000;
