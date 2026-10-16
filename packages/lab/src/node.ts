// The lab in Node, for checks that run outside a browser: Pyodide from the files
// `pnpm --filter @sulba/lab pyodide` puts together, and CPython through uv.
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadPyodide } from 'pyodide';
import { pyodideFolder } from './assemble.ts';
import { createEngine, type Engine } from './engine.ts';
import {
  type ChartRequest,
  type ChartResult,
  type Figures,
  pythonPackages,
  type RunRequest,
  type RunResult,
  statusOf,
} from './protocol.ts';

export type { Engine } from './engine.ts';

const python = fileURLToPath(new URL('../python/', import.meta.url));

/** Pyodide with every package sessions can use already loaded. */
export async function pyodideEngine(): Promise<Engine> {
  const runner = await readFile(new URL('../python/sulba_runner.py', import.meta.url), 'utf8');
  const pyodide = await loadPyodide({ indexURL: pyodideFolder, packageCacheDir: pyodideFolder });
  const engine = await createEngine(pyodide, runner);
  await engine.load(pythonPackages);
  return engine;
}

/**
 * A hash of what an answer from `pyodideEngine` depends on besides the files it is given: the
 * runner, and Pyodide's lock file, which holds the version of every package.
 */
export async function pyodideRuntime(): Promise<string> {
  const runner = await readFile(new URL('../python/sulba_runner.py', import.meta.url), 'utf8');
  const lock = await readFile(join(pyodideFolder, 'pyodide-lock.json'), 'utf8');
  return createHash('sha256').update(runner).update('\0').update(lock).digest('hex');
}

/** A CPython process ended for running past its time limit. */
class TimeLimit extends Error {}

/**
 * Send each request to one CPython process, at the versions in python/uv.lock, and read back an
 * answer per line. With `limitMs`, a process still running then is ended, and nothing comes back.
 */
function inCPython(requests: readonly object[], limitMs?: number): Promise<unknown[]> {
  return new Promise((resolve, reject) => {
    const child = spawn('uv', ['run', '--directory', python, 'python', 'sulba_runner.py'], {
      stdio: ['pipe', 'pipe', 'inherit'],
    });
    let out = '';
    let late = false;
    const timer =
      limitMs === undefined
        ? undefined
        : setTimeout(() => {
            late = true;
            child.kill();
          }, limitMs);
    child.stdout.setEncoding('utf8').on('data', (chunk: string) => {
      out += chunk;
    });
    child.on('error', (error) => reject(new Error(`uv didn't start (${error.message}).`)));
    child.on('close', (code) => {
      clearTimeout(timer);
      if (late) return reject(new TimeLimit());
      if (code !== 0) return reject(new Error(`CPython stopped with code ${code}.`));
      const answers = out
        .split('\n')
        .filter((line) => line.trim() !== '')
        .map((line) => JSON.parse(line) as unknown);
      if (answers.length !== requests.length) {
        return reject(
          new Error(`CPython gave ${answers.length} answers for ${requests.length} requests.`),
        );
      }
      resolve(answers);
    });
    for (const request of requests) child.stdin.write(`${JSON.stringify(request)}\n`);
    child.stdin.end();
  });
}

/** Run each request in CPython. */
export async function runInCPython(
  requests: readonly RunRequest[],
  limitMs?: number,
): Promise<RunResult[]> {
  const answers = await inCPython(
    requests.map(({ files, tests }) => ({ files, tests })),
    limitMs,
  );
  return answers.map((answer) => {
    const outcome = answer as Omit<RunResult, 'status'>;
    return { status: statusOf(outcome.tests, outcome.problem), ...outcome };
  });
}

/**
 * Run each request in a CPython process of its own, and stop one still running after `limitMs`,
 * as the browser stops a run, so code that never ends can't hold up the rest. Starting a process
 * for each request makes this slower than runInCPython.
 */
export async function runEachInCPython(
  requests: readonly RunRequest[],
  limitMs: number,
): Promise<RunResult[]> {
  const results: RunResult[] = [];
  for (const request of requests) {
    try {
      results.push(...(await runInCPython([request], limitMs)));
    } catch (error) {
      if (!(error instanceof TimeLimit)) throw error;
      const message = `Stopped after ${limitMs / 1000} seconds.`;
      results.push({
        status: 'error',
        tests: [],
        problem: { kind: 'TimeLimit', message, location: null },
        output: '',
        durationMs: limitMs,
      });
    }
  }
  return results;
}

/** Each set of files' figures, computed in CPython. */
export async function figuresInCPython(
  fileSets: readonly RunRequest['files'][],
): Promise<Figures[]> {
  const answers = await inCPython(fileSets.map((files) => ({ files, figures: true })));
  return answers as Figures[];
}

/** What each request's chart.py draws, in CPython. */
export async function chartsInCPython(requests: readonly ChartRequest[]): Promise<ChartResult[]> {
  const answers = await inCPython(requests.map(({ files, values }) => ({ files, chart: values })));
  return answers as ChartResult[];
}
