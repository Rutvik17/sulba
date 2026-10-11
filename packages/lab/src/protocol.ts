/**
 * The run protocol every runner speaks: files and tests go in, a result per test comes out. The
 * workspace never knows which runner answered (decision record 5).
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

/** The Python packages sessions can load, from Pyodide's builds. pytest is always loaded. */
export const pythonPackages = ['numpy'] as const;
export type PythonPackage = (typeof pythonPackages)[number];

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
