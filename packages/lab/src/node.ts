// The lab in Node, for checks that run outside a browser: Pyodide from the files
// `pnpm --filter @sulba/lab pyodide` puts together, and CPython through uv.
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadPyodide } from 'pyodide';
import { pyodideFolder } from './assemble.ts';
import { createEngine, type Engine, type RunnerModules } from './engine.ts';
import { runnerFolder } from './machine.ts';
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

/** The runner's Python modules, as the files in python/ hold them. */
async function runnerModules(): Promise<RunnerModules> {
  const text = (name: string) => readFile(join(python, name), 'utf8');
  const [runner, fixtures] = await Promise.all([
    text('sulba_runner.py'),
    text('sulba_fixtures.py'),
  ]);
  return { 'sulba_runner.py': runner, 'sulba_fixtures.py': fixtures };
}

/**
 * The runner a machine lab's download carries (decision record 28), each file by its path in the
 * download: sulba.py at its top, and the runner's modules in its runner folder.
 */
export async function runnerFiles(): Promise<Record<string, string>> {
  const modules = await runnerModules();
  return {
    'sulba.py': await readFile(join(python, 'sulba.py'), 'utf8'),
    ...Object.fromEntries(
      Object.entries(modules).map(([name, text]) => [`${runnerFolder}/${name}`, text]),
    ),
  };
}

/** Pyodide with every package sessions can use already loaded. */
export async function pyodideEngine(): Promise<Engine> {
  const pyodide = await loadPyodide({ indexURL: pyodideFolder, packageCacheDir: pyodideFolder });
  const engine = await createEngine(pyodide, await runnerModules());
  await engine.load(pythonPackages);
  return engine;
}

/**
 * A hash of what an answer from `pyodideEngine` depends on besides the files it is given: the
 * runner's modules, and Pyodide's lock file, which holds the version of every package.
 */
export async function pyodideRuntime(): Promise<string> {
  const runner = await runnerModules();
  const lock = await readFile(join(pyodideFolder, 'pyodide-lock.json'), 'utf8');
  const hash = createHash('sha256');
  for (const text of [runner['sulba_runner.py'], runner['sulba_fixtures.py'], lock]) {
    hash.update(text).update('\0');
  }
  return hash.digest('hex');
}

/**
 * A hash of what an answer from CPython in a machine lab's project depends on besides its files:
 * the runner's modules, and the project's uv.lock, which holds the version of every package.
 */
export async function projectRuntime(lock: string): Promise<string> {
  const runner = await runnerModules();
  const hash = createHash('sha256');
  for (const text of [runner['sulba_runner.py'], runner['sulba_fixtures.py'], lock]) {
    hash.update(text).update('\0');
  }
  return hash.digest('hex');
}

/** A CPython process ended for running past its time limit. */
class TimeLimit extends Error {}

/**
 * Send each request to one CPython process, at the versions in python/uv.lock or, with `project`,
 * in that machine lab's project, at the versions its uv.lock pins (decision record 28), and read
 * back an answer per line. With `limitMs`, a process still running then is ended, and nothing
 * comes back.
 */
function inCPython(
  requests: readonly object[],
  limitMs?: number,
  project?: string,
): Promise<unknown[]> {
  return new Promise((resolve, reject) => {
    const where = project === undefined ? [] : ['--project', project];
    const child = spawn(
      'uv',
      ['run', ...where, '--directory', python, 'python', 'sulba_runner.py'],
      {
        stdio: ['pipe', 'pipe', 'inherit'],
      },
    );
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

/** Run each request in CPython, in a machine lab's project when one is given. */
export async function runInCPython(
  requests: readonly RunRequest[],
  limitMs?: number,
  project?: string,
): Promise<RunResult[]> {
  const answers = await inCPython(
    requests.map(({ files, tests }) => ({ files, tests })),
    limitMs,
    project,
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

/** Each set of files' figures, computed in CPython, in a machine lab's project when one is given. */
export async function figuresInCPython(
  fileSets: readonly RunRequest['files'][],
  project?: string,
): Promise<Figures[]> {
  const answers = await inCPython(
    fileSets.map((files) => ({ files, figures: true })),
    undefined,
    project,
  );
  return answers as Figures[];
}

/** What each request's chart.py draws, in CPython. */
export async function chartsInCPython(requests: readonly ChartRequest[]): Promise<ChartResult[]> {
  const answers = await inCPython(requests.map(({ files, values }) => ({ files, chart: values })));
  return answers as ChartResult[];
}
