// "How every lab runs" on the landing: one lab frame, pinned, that moves only while the reader
// scrolls. Each stage gets about one screen of scrolling, and a few seconds of action within it:
// Build types a function and its tests pass, Catch fixes one of the assistant's mistakes and a
// production check passes, Ship rewrites a slow search and the code is ready. Every frame is a
// function of the scroll position, so it can run forwards or backwards and be tested.

export const stages = [
  {
    id: 'build',
    name: 'Build',
    text: 'Write the core of each system by hand, so you know how it works underneath.',
  },
  {
    id: 'catch',
    name: 'Catch',
    text: "An assistant's code that uses yours passes its own tests. Find and fix what it would get wrong in real use.",
  },
  {
    id: 'ship',
    name: 'Ship',
    text: 'Put your code to work on a real decision. It ships when hidden tests and production checks pass.',
  },
] as const;

export type StageId = (typeof stages)[number]['id'];
export type TestState = 'idle' | 'running' | 'pass' | 'fail';

/** A run of code in one style: a keyword, a function name, a string, or plain text. */
export interface Run {
  text: string;
  kind?: 'kw' | 'fn' | 'str';
  /** When a narrow frame wraps the line, this run stays on one line. */
  keep?: boolean;
}

/** A line of code as runs, after its indent. */
export interface Line {
  indent: number;
  runs: readonly Run[];
}

const kw = (text: string): Run => ({ text, kind: 'kw' });
const fn = (text: string): Run => ({ text, kind: 'fn' });
const str = (text: string): Run => ({ text, kind: 'str' });
const t = (text: string): Run => ({ text });
const keep = (text: string): Run => ({ text, keep: true });

// Build: the sigmoid, written into model.py. Its tests are the first four of the lab's.
export const build = {
  file: 'model.py',
  head: { indent: 0, runs: [kw('def '), fn('sigmoid'), t('(z):')] } as Line,
  body: [
    { indent: 1, runs: [t('z = np.asarray(z, dtype=float)')] },
    { indent: 1, runs: [t('out = np.empty_like(z)')] },
    { indent: 1, runs: [t('positive = z >= 0')] },
    // Wrapped, the minus sign stays with its z.
    { indent: 1, runs: [t('out[positive] = 1.0 / (1.0 + '), keep('np.exp(-z[positive]))')] },
    { indent: 1, runs: [t('ez = np.exp(z[~positive])')] },
    { indent: 1, runs: [t('out[~positive] = ez / (1.0 + ez)')] },
    { indent: 1, runs: [kw('return'), t(' out')] },
  ] as readonly Line[],
  tests: [
    'Half at zero',
    'On an array',
    "Big inputs don't overflow",
    'Symmetric about zero',
  ] as const,
};

// Catch: the assistant's screener rescales each batch with its own numbers (training-serving
// skew). Deleting "fit_" makes it reuse the numbers fit learned, and one more check passes.
export const catchStage = {
  file: 'screener.py',
  lines: [
    { indent: 0, runs: [kw('def '), fn('score'), t('(self, X_new):')] },
    { indent: 1, runs: [str('"""The probability that each new sample is malignant."""')] },
  ] as readonly Line[],
  before: '    X_new = self.scaler.',
  removed: 'fit_',
  after: 'transform(self.imputer.transform(X_new))',
  last: { indent: 1, runs: [kw('return'), t(' self.model.predict_proba(X_new)[:, 0]')] } as Line,
  tests: [
    'One probability per sample',
    'Every probability is between 0 and 1',
    'The model is at least 90% accurate on the test set',
  ] as const,
  checks: 5,
};

// Ship: a threshold search that is right but tries every value is rewritten to sort once.
export const ship = {
  file: 'screener.py',
  head: {
    indent: 0,
    runs: [kw('def '), fn('best_threshold'), t('(y, p, min_recall):')],
  } as Line,
  slow: [
    { indent: 1, runs: [kw('for'), t(' t '), kw('in'), t(' np.sort(np.unique(p))[::-1]:')] },
    { indent: 2, runs: [kw('if'), t(' np.mean(p[y == 1] >= t) >= min_recall:')] },
    { indent: 3, runs: [kw('return'), t(' float(t)')] },
  ] as readonly Line[],
  fast: [
    { indent: 1, runs: [t('positives = np.sort(p[y == 1])[::-1]')] },
    { indent: 1, runs: [t('needed = max(1, int(np.ceil(min_recall * len(positives) - 1e-9)))')] },
    { indent: 1, runs: [kw('return'), t(' float(positives[needed - 1])')] },
  ] as readonly Line[],
  hidden: 6,
  checks: ['Fast on 200,000 samples', 'Leaves the arrays it is given unchanged'] as const,
};

/** The most lines of code any stage shows. Every stage's editor is that tall, so the tests under
 * it stay put when the stage changes. */
export const mostLines = Math.max(
  1 + build.body.length,
  catchStage.lines.length + 2,
  1 + Math.max(ship.slow.length, ship.fast.length),
);

export const lineText = (line: Line) =>
  '    '.repeat(line.indent) + line.runs.map((r) => r.text).join('');
/** Characters typed for these lines: their runs, not the indent, which is there from the start. */
export const typedLength = (lines: readonly Line[]) =>
  lines.reduce((n, l) => n + l.runs.reduce((m, r) => m + r.text.length, 0), 0);

/** Where the scroll is: which stage, and how far into it, from 0 to 1. */
export function stageAt(progress: number): { stage: number; local: number } {
  const p = Math.min(Math.max(progress, 0), 1) * stages.length;
  const stage = Math.min(stages.length - 1, Math.floor(p));
  return { stage, local: Math.min(1, p - stage) };
}

/** Where to scroll for the start of a stage, as overall progress. */
export const stageStart = (stage: number) => (stage + 0.02) / stages.length;

// Within a stage, its action runs between these points; before and after, it holds still.
const span = (local: number, from: number, to: number) =>
  Math.min(1, Math.max(0, (local - from) / (to - from)));

/** Tests that turn one after another between two points. */
function turning(count: number, local: number, from: number, to: number, end: TestState = 'pass') {
  const each = (to - from) / count;
  return Array.from({ length: count }, (_, i): TestState => {
    const start = from + i * each;
    return local < start ? 'idle' : local < start + each * 0.7 ? 'running' : end;
  });
}

export interface BuildFrame {
  /** Characters of the body typed so far. */
  typed: number;
  tests: TestState[];
  done: boolean;
}

export function buildAt(local: number): BuildFrame {
  const total = typedLength(build.body);
  return {
    typed: Math.round(total * span(local, 0.06, 0.58)),
    tests: turning(build.tests.length, local, 0.64, 0.86),
    done: local >= 0.9,
  };
}

export type ChecksLine = 'idle' | 'running' | 'none' | 'one';

export interface CatchFrame {
  tests: TestState[];
  checks: ChecksLine;
  /** Characters of "fit_" selected. */
  selected: number;
  removed: boolean;
}

export function catchAt(local: number): CatchFrame {
  const rerun = local >= 0.66;
  return {
    tests: rerun
      ? turning(catchStage.tests.length, local, 0.66, 0.78)
      : turning(catchStage.tests.length, local, 0.06, 0.2),
    checks: rerun
      ? local >= 0.84
        ? 'one'
        : 'running'
      : local >= 0.26
        ? 'none'
        : local >= 0.06
          ? 'running'
          : 'idle',
    selected: local >= 0.52 ? 0 : Math.round(catchStage.removed.length * span(local, 0.36, 0.48)),
    removed: local >= 0.52,
  };
}

export interface ShipFrame {
  hidden: TestState;
  checks: TestState[];
  /** The slow loop is selected, then gone. */
  selected: boolean;
  removed: boolean;
  /** Characters of the new body typed so far. */
  typed: number;
  ready: boolean;
}

export function shipAt(local: number): ShipFrame {
  const rerun = local >= 0.78;
  const first = local >= 0.06;
  return {
    hidden: !first ? 'idle' : local < 0.14 ? 'running' : rerun && local < 0.84 ? 'running' : 'pass',
    checks: rerun
      ? turning(ship.checks.length, local, 0.84, 0.92)
      : first
        ? [local < 0.2 ? 'running' : 'fail', local < 0.22 ? 'running' : 'pass']
        : ['idle', 'idle'],
    selected: local >= 0.32 && local < 0.4,
    removed: local >= 0.4,
    typed: Math.round(typedLength(ship.fast) * span(local, 0.42, 0.74)),
    ready: local >= 0.94,
  };
}
