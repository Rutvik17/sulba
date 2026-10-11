// Runs tests in a loaded Pyodide. The worker uses it in the browser and node.ts uses it in Node,
// so both go through the same steps.
import type { PyodideAPI } from 'pyodide';
import { type RunRequest, type RunResult, statusOf } from './protocol.ts';

type Outcome = Omit<RunResult, 'status'>;

export interface Engine {
  /** Load packages a run will need, so loading isn't counted in the run's time. */
  load(packages: RunRequest['packages']): Promise<void>;
  run(request: RunRequest): RunResult;
}

/** `runner` is the text of python/sulba_runner.py. */
export async function createEngine(pyodide: PyodideAPI, runner: string): Promise<Engine> {
  const quiet = { messageCallback: () => {} };
  await pyodide.loadPackage('pytest', quiet);
  pyodide.FS.mkdirTree('/sulba');
  pyodide.FS.writeFile('/sulba/sulba_runner.py', runner);
  pyodide.runPython('import sys\nsys.path.insert(0, "/sulba")');
  const run = pyodide.pyimport('sulba_runner').run as (files: string, tests: string) => string;
  return {
    load: (packages) => pyodide.loadPackage([...packages], quiet).then(() => undefined),
    run(request) {
      const outcome = JSON.parse(
        run(JSON.stringify(request.files), JSON.stringify(request.tests)),
      ) as Outcome;
      return { status: statusOf(outcome.tests, outcome.problem), ...outcome };
    },
  };
}
