// The lab in Node, for checks that run outside a browser: Pyodide from the files
// `pnpm --filter @sulba/lab pyodide` puts together, and CPython through uv.
import { spawn } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { loadPyodide } from 'pyodide';
import { createEngine, type Engine } from './engine.ts';
import { pythonPackages, type RunRequest, type RunResult, statusOf } from './protocol.ts';

const python = fileURLToPath(new URL('../python/', import.meta.url));
const indexURL = fileURLToPath(new URL('../pyodide/', import.meta.url));

/** Pyodide with every package sessions can use already loaded. */
export async function pyodideEngine(): Promise<Engine> {
  const runner = await readFile(new URL('../python/sulba_runner.py', import.meta.url), 'utf8');
  const pyodide = await loadPyodide({ indexURL, packageCacheDir: indexURL });
  const engine = await createEngine(pyodide, runner);
  await engine.load(pythonPackages);
  return engine;
}

/** Run each request in CPython, at the versions in python/uv.lock, in one process. */
export function runInCPython(requests: readonly RunRequest[]): Promise<RunResult[]> {
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
      const results = out
        .split('\n')
        .filter((line) => line.trim() !== '')
        .map((line) => {
          const outcome = JSON.parse(line) as Omit<RunResult, 'status'>;
          return { status: statusOf(outcome.tests, outcome.problem), ...outcome };
        });
      if (results.length !== requests.length) {
        return reject(
          new Error(`CPython gave ${results.length} results for ${requests.length} runs.`),
        );
      }
      resolve(results);
    });
    for (const { files, tests } of requests) {
      child.stdin.write(`${JSON.stringify({ files, tests })}\n`);
    }
    child.stdin.end();
  });
}
