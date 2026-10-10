// Fig. 1 on the landing, a Catch stage: an assistant wrote the order-lookup tool a support agent
// calls. Its own two tests pass, but it pastes the customer's name into its SQL, so one of two
// production checks fails. The learner turns the query into a parameterised one, and both checks
// pass. Every frame is a function of one clock, so the player can pause, replay, hold the last
// frame for reduced motion, and be tested. It plays once and rests on its last frame.

/** The tool's query, up to where the customer's name goes. */
export const select = 'SELECT id, total FROM orders WHERE customer = ';

/** A name that closes the quote and adds a condition that is always true. */
export const injection = "x' OR '1'='1";

/** The tests the assistant wrote. Both pass, before and after the fix. */
export const assistantTests = [
  "Finds a customer's orders",
  'Returns nothing for an unknown name',
] as const;

/** The production checks. Hidden while the learner reviews; the first fails until the fix. */
export const checks = ['Treats a name as text, not SQL', 'Returns only ids and totals'] as const;

/**
 * The learner's three edits, in order: delete the f that makes the query an f-string, replace the
 * quoted name with a placeholder, and pass the name to execute() as a parameter.
 */
export const edits = {
  a: { remove: 'f', insert: '' },
  b: { remove: "'{name}'", insert: '?' },
  c: { remove: '', insert: ', (name,)' },
} as const;

export type EditId = keyof typeof edits;
export type Place = 'rest' | 'run' | 'a' | 'a-end' | 'b' | 'b-sel' | 'b-end' | 'c' | 'c-end';
export type TestState = 'idle' | 'running' | 'pass' | 'fail';
export type Checks = 'idle' | 'running' | 'some' | 'all';

const CHAR = 55;

// Milliseconds from the start.
export const at = {
  press1: 1500,
  results1: 1700,
  checked1: 2440,
  clickA: 3800,
  deleteA: 4050,
  pressB: 4900,
  typeB: 5550,
  clickC: 6500,
  typeC: 6650,
  press2: 8400,
  results2: 8600,
  checked2: 9320,
  done: 9600,
} as const;

/** Where the clip ends and rests: the review done, both checks passing, the pointer still. */
export const END = 10_800;

// The pointer's journey in straight lines: [start, end, from, to]. After typing it comes back
// where the typing ended, as if the hand had followed the caret.
const moves: readonly (readonly [number, number, Place, Place])[] = [
  [600, 1450, 'rest', 'run'],
  [3000, 3800, 'run', 'a'],
  [4400, 4900, 'a-end', 'b'],
  [5000, 5350, 'b', 'b-sel'],
  [5900, 6500, 'b-end', 'c'],
  [7700, 8350, 'c-end', 'run'],
  [9700, 10_500, 'run', 'rest'],
];

// The mouse button is down: clicks, and the drag that selects the quoted name.
const presses: readonly (readonly [number, number])[] = [
  [at.press1, at.press1 + 120],
  [at.clickA, at.clickA + 100],
  [at.pressB, 5350],
  [at.clickC, at.clickC + 100],
  [at.press2, at.press2 + 120],
];

// As on macOS and Windows, the pointer hides while you type and comes back when it moves.
const typing: readonly (readonly [number, number])[] = [
  [at.deleteA, 4400],
  [at.typeB, 5900],
  [at.typeC, 7700],
];

export const checkLines: Record<Checks, string> = {
  idle: 'Not run yet',
  running: 'Running…',
  some: `1 of ${checks.length} pass`,
  all: `${checks.length} of ${checks.length} pass`,
};

export interface EditFrame {
  /** The text to remove is gone. */
  removed: boolean;
  /** How many characters of the text to remove are selected. */
  selected: number;
  /** How many characters of the insertion are typed. */
  typed: number;
  /** Just typed, so it is highlighted. */
  fresh: boolean;
}

export interface Frame {
  edits: Record<EditId, EditFrame>;
  caret: EditId | null;
  typing: boolean;
  blink: boolean;
  away: boolean;
  tests: TestState[];
  checks: Checks;
  /** The note that the failing check stays hidden until the review is finished. */
  hiddenNote: boolean;
  done: boolean;
  /** The Run tests button is held down. */
  down: boolean;
  /** The mouse button is down. */
  press: boolean;
  pointer: { from: Place; to: Place; k: number };
}

const ease = (x: number) => (x < 0.5 ? 4 * x ** 3 : 1 - (-2 * x + 2) ** 3 / 2);
const within = (t: number, [start, end]: readonly [number, number]) => t >= start && t < end;

function pointerAt(t: number): Frame['pointer'] {
  let place: Frame['pointer'] = { from: 'rest', to: 'rest', k: 1 };
  for (const [start, end, from, to] of moves) {
    if (t < start) break;
    place = { from, to, k: t >= end ? 1 : ease((t - start) / (end - start)) };
  }
  return place;
}

export function frameAt(clock: number): Frame {
  const t = Math.min(clock, END);
  const pointer = pointerAt(t);
  const second = t >= at.press2 + 120;
  const typed = (start: number, text: string) =>
    t < start ? 0 : Math.min(text.length, Math.floor((t - start) / CHAR) + 1);
  const dragging = pointer.from === 'b' && pointer.to === 'b-sel';
  const selectedB =
    t >= at.typeB || t < at.pressB
      ? 0
      : dragging
        ? Math.round(edits.b.remove.length * pointer.k)
        : edits.b.remove.length;
  const run = second ? at.results2 : at.results1;

  return {
    edits: {
      a: { removed: t >= at.deleteA, selected: 0, typed: 0, fresh: false },
      b: {
        removed: t >= at.typeB,
        selected: selectedB,
        typed: typed(at.typeB, edits.b.insert),
        fresh: t >= at.typeB && t < at.typeB + 1600,
      },
      c: {
        removed: false,
        selected: 0,
        typed: typed(at.typeC, edits.c.insert),
        fresh: t >= at.typeC && t < at.typeC + 1600,
      },
    },
    caret:
      t >= at.clickA + 50 && t < at.pressB
        ? 'a'
        : t >= at.typeB && t < at.clickC
          ? 'b'
          : t >= at.clickC + 50 && t < at.press2
            ? 'c'
            : null,
    typing:
      within(t, [at.deleteA, at.deleteA + CHAR]) ||
      within(t, [at.typeB, at.typeB + CHAR]) ||
      within(t, [at.typeC, at.typeC + edits.c.insert.length * CHAR]),
    blink: Math.floor(t / 530) % 2 === 0,
    away: typing.some((span) => within(t, span)),
    tests: assistantTests.map((_, i) => {
      const start = run + i * 220;
      return t < start ? 'idle' : t < start + 200 ? 'running' : 'pass';
    }),
    checks: second
      ? t >= at.checked2
        ? 'all'
        : 'running'
      : t >= at.checked1
        ? 'some'
        : t >= at.press1 + 120
          ? 'running'
          : 'idle',
    hiddenNote: t >= at.checked1 + 120 && !second,
    done: t >= at.done,
    down: [at.press1, at.press2].some((press) => within(t, [press, press + 120])),
    press: presses.some((span) => within(t, span)),
    pointer,
  };
}
