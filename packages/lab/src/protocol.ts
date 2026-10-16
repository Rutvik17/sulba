/**
 * The run protocol every runner speaks: files and tests go in, a result per test comes out. The
 * workspace never knows which runner answered (decision record 17).
 */

/** Run these test files against these files. */
export interface RunRequest {
  /** Every file the run needs, by its path inside the session, such as `tests/test_model.py`. */
  readonly files: Readonly<Record<string, string>>;
  /** The test files to run, in order. */
  readonly tests: readonly string[];
  /** Python packages to load before the run, from `pythonPackages`. */
  readonly packages: readonly PythonPackage[];
}

/** Where in the learner's files something happened. */
export interface Location {
  readonly file: string;
  /** Counted from 1. */
  readonly line: number;
}

export interface TestResult {
  /** The test's permanent id. */
  readonly id: string | null;
  readonly name: string;
  /** fail: a check didn't hold. error: the code raised an error before the check. */
  readonly status: 'pass' | 'fail' | 'error';
  readonly message: string | null;
  /** Both sides of a failed comparison, as Python shows them. */
  readonly expected: string | null;
  readonly actual: string | null;
  readonly location: Location | null;
  /** What the test printed. */
  readonly output: string;
  /**
   * What the test reports beyond passing or failing, such as how long the code took: the value it
   * gave `record_property("note", ...)`.
   */
  readonly note: string | null;
  readonly durationMs: number;
}

/** Why no test ran: the code didn't load, or the run was stopped. */
export interface Problem {
  /** The Python error's type, such as SyntaxError, or TimeLimit when the run was stopped. */
  readonly kind: string;
  readonly message: string;
  readonly location: Location | null;
}

export interface RunResult {
  /** pass: every test passed. fail: at least one didn't. error: no test ran. */
  readonly status: 'pass' | 'fail' | 'error';
  readonly tests: readonly TestResult[];
  readonly problem: Problem | null;
  /** What the code printed while it loaded, outside any test. */
  readonly output: string;
  readonly durationMs: number;
}

/** The numbers a stage's figures.py gives, by name, or why it gave none. */
export interface Figures {
  readonly figures: Readonly<Record<string, string>> | null;
  readonly problem: string | null;
}

/** Draw a stage's chart: call chart() in its chart.py, among these files, with these values. */
export interface ChartRequest {
  /** chart.py and every file it reads, such as the learner's code and the lab's data. */
  readonly files: RunRequest['files'];
  /** Each slider's value, by the name chart() takes it as. */
  readonly values: Readonly<Record<string, number>>;
  readonly packages: RunRequest['packages'];
}

/**
 * How a line is drawn. main: the learner's own result. base: a curve the learner's result is read
 * against. faint: a result to compare with. dashed: a level, such as the lowest loss there is.
 */
export const lineStyles = ['main', 'base', 'faint', 'dashed'] as const;
export type LineStyle = (typeof lineStyles)[number];

/** An axis: the values it spans, the step between its labelled ticks, and what it measures. */
export interface Axis {
  readonly min: number;
  readonly max: number;
  readonly step: number;
  readonly label: string;
}

export interface Line {
  readonly style: LineStyle;
  /** What the line shows, as the legend names it. */
  readonly label: string;
  readonly x: readonly number[];
  /** Null where there is no number, such as a loss that isn't finite: the line breaks there. */
  readonly y: readonly (number | null)[];
}

/** What a stage's chart.py draws, and the values to read beside it. */
export interface Drawing {
  readonly x: Axis;
  readonly y: Axis;
  /** In the order they are drawn, so a later line lies on top. The legend lists the top one first. */
  readonly lines: readonly Line[];
  /** Points marked on top, in the main style. */
  readonly points: readonly { readonly x: number; readonly y: number | null }[];
  /** Each value with the expression that gives it, such as `sigmoid(1 * 0 + 0)`. */
  readonly readouts: readonly { readonly label: string; readonly value: string }[];
  /** What the chart shows, for screen readers. */
  readonly description: string;
}

/** What a chart drew, or why it drew nothing: chart.py's error, or TimeLimit when it was stopped. */
export interface ChartResult {
  readonly chart: Drawing | null;
  readonly problem: Pick<Problem, 'kind' | 'message'> | null;
}

/** The Python packages sessions can load, from Pyodide's builds. pytest is always loaded. */
export const pythonPackages = [
  'numpy',
  'pandas',
  'scipy',
  'scikit-learn',
  'xgboost',
  'lightgbm',
  'regex',
  'tiktoken',
  'mypy',
  'packaging',
] as const;
export type PythonPackage = (typeof pythonPackages)[number];

/** The module each package is imported as. */
export const importNames: Readonly<Record<PythonPackage, string>> = {
  numpy: 'numpy',
  pandas: 'pandas',
  scipy: 'scipy',
  'scikit-learn': 'sklearn',
  xgboost: 'xgboost',
  lightgbm: 'lightgbm',
  regex: 'regex',
  tiktoken: 'tiktoken',
  mypy: 'mypy',
  packaging: 'packaging',
};

/** The Pyodide release sessions run on. A test holds it to the npm package's version. */
export const pyodideVersion = '314.0.7';

/** Where the site serves Pyodide's files, a folder per release so each can be cached for good. */
export const pyodidePath = `/pyodide/${pyodideVersion}/`;

/** How long a run may take before it is stopped. A loop that never ends stops here. */
export const timeLimitMs = 5000;

/** The status a run's tests and problem add up to. */
export function statusOf(
  tests: readonly TestResult[],
  problem: Problem | null,
): RunResult['status'] {
  if (problem || tests.length === 0) return 'error';
  return tests.every((test) => test.status === 'pass') ? 'pass' : 'fail';
}
