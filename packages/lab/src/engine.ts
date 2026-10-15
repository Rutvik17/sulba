// Runs tests in a loaded Pyodide. The worker uses it in the browser and node.ts uses it in Node,
// so both go through the same steps.
import type { PyodideAPI } from 'pyodide';
import {
  type ChartRequest,
  type ChartResult,
  type Figures,
  importNames,
  type RunRequest,
  type RunResult,
  statusOf,
} from './protocol.ts';

type Outcome = Omit<RunResult, 'status'>;

export interface Engine {
  /** Load packages a run will need, so loading isn't counted in the run's time. */
  load(packages: RunRequest['packages']): Promise<void>;
  /**
   * Import the modules a request's files import from its packages, which must be loaded, so
   * importing them isn't counted in its time either.
   */
  prepare(request: Pick<RunRequest, 'files' | 'packages'>): void;
  run(request: RunRequest): RunResult;
  /** The numbers the files' figures.py gives, for prose to show. */
  figures(files: RunRequest['files']): Figures;
  /** What the files' chart.py draws with these values. Its packages must be loaded. */
  chart(request: Omit<ChartRequest, 'packages'>): ChartResult;
}

/** `runner` is the text of python/sulba_runner.py. */
export async function createEngine(pyodide: PyodideAPI, runner: string): Promise<Engine> {
  const quiet = { messageCallback: () => {} };
  await pyodide.loadPackage('pytest', quiet);
  pyodide.FS.mkdirTree('/sulba');
  pyodide.FS.writeFile('/sulba/sulba_runner.py', runner);
  pyodide.runPython('import sys\nsys.path.insert(0, "/sulba")');
  const module = pyodide.pyimport('sulba_runner');
  const run = module.run as (files: string, tests: string) => string;
  const prepare = module.prepare as (files: string, packages: string) => void;
  const figures = module.figures as (files: string) => string;
  const chart = module.chart as (files: string, values: string) => string;
  return {
    async load(packages) {
      await pyodide.loadPackage([...packages], quiet);
      // Importing is part of loading: scikit-learn takes seconds to import the first time.
      for (const name of packages) pyodide.runPython(`import ${importNames[name]}`);
    },
    prepare({ files, packages }) {
      // Importing a package doesn't import all of it: SciPy loads scipy.stats when it is first
      // imported, which takes seconds in a browser.
      prepare(JSON.stringify(files), JSON.stringify(packages.map((name) => importNames[name])));
    },
    run(request) {
      const outcome = JSON.parse(
        run(JSON.stringify(request.files), JSON.stringify(request.tests)),
      ) as Outcome;
      return { status: statusOf(outcome.tests, outcome.problem), ...outcome };
    },
    figures: (files) => JSON.parse(figures(JSON.stringify(files))) as Figures,
    chart: ({ files, values }) =>
      JSON.parse(chart(JSON.stringify(files), JSON.stringify(values))) as ChartResult,
  };
}
