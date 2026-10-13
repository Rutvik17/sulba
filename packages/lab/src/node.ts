// The lab in Node, for checks that run outside a browser: Pyodide from the files
// `pnpm --filter @sulba/lab pyodide` puts together, and CPython through uv.
import { spawn } from 'node:child_process';
import { readFile } from 'node:fs/promises';
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

/** Send each request to one CPython process, at the versions in python/uv.lock, and read back an answer per line. */
function inCPython(requests: readonly object[]): Promise<unknown[]> {
  return new Promise((resolve, reject) => {
    const child = spawn('uv', ['run', '--directory', python, 'python', 'sulba_runner.py'], {
      stdio: ['pipe', 'pipe', 'inherit'],
    });
    let out = '';
    child.stdout.setEncoding('utf8').on('data', (chunk: string) => {
      out += chunk;
    });
    child.on('error', (error) => reject(new Error(`uv didn't start (${error.message}).`)));
    child.on('close', (code) => {
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
export async function runInCPython(requests: readonly RunRequest[]): Promise<RunResult[]> {
  const answers = await inCPython(requests.map(({ files, tests }) => ({ files, tests })));
  return answers.map((answer) => {
    const outcome = answer as Omit<RunResult, 'status'>;
    return { status: statusOf(outcome.tests, outcome.problem), ...outcome };
  });
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
