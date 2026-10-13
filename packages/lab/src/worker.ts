// The lab's Web Worker. It loads Pyodide from Sulba's own domain, then does one task at a time
// for the page. Python runs on this thread, so the page can always stop a run by ending it.
import type { loadPyodide } from 'pyodide';
import runner from '../python/sulba_runner.py?raw';
import { createEngine, type Engine } from './engine.ts';
import type { FromWorker, ToWorker } from './messages.ts';

interface Scope {
  postMessage(message: FromWorker): void;
  addEventListener(type: 'message', listener: (event: MessageEvent<ToWorker>) => void): void;
}

const scope = self as unknown as Scope;
let engine: Promise<Engine> | undefined;

async function start(indexURL: string): Promise<Engine> {
  // Pyodide loads its other files from beside this one, so it comes from the same folder.
  const module = (await import(/* @vite-ignore */ `${indexURL}pyodide.mjs`)) as {
    loadPyodide: typeof loadPyodide;
  };
  const pyodide = await module.loadPyodide({ indexURL, stdout: () => {}, stderr: () => {} });
  return createEngine(pyodide, runner);
}

function failed(id: number | null, error: unknown) {
  scope.postMessage({ type: 'failed', id, message: String(error) });
}

scope.addEventListener('message', ({ data }) => {
  if (data.type === 'start') {
    engine = start(data.indexURL);
    engine.catch((error: unknown) => failed(null, error));
    return;
  }
  const { id } = data;
  if (!engine) return failed(id, 'The lab was asked to work before it started.');
  engine
    .then(async (ready) => {
      if (data.type === 'load') {
        await ready.load(data.packages);
        return scope.postMessage({ type: 'loaded', id });
      }
      await ready.load(data.request.packages);
      scope.postMessage({ type: 'started', id });
      if (data.type === 'chart') {
        return scope.postMessage({ type: 'drawn', id, result: ready.chart(data.request) });
      }
      scope.postMessage({ type: 'result', id, result: ready.run(data.request) });
    })
    .catch((error: unknown) => failed(id, error));
});
