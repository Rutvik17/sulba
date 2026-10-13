// What the page and the lab's worker say to each other.
import type { ChartRequest, ChartResult, RunRequest, RunResult } from './protocol.ts';

export type ToWorker =
  | { readonly type: 'start'; readonly indexURL: string }
  | { readonly type: 'load'; readonly id: number; readonly packages: RunRequest['packages'] }
  | { readonly type: 'run'; readonly id: number; readonly request: RunRequest }
  | { readonly type: 'chart'; readonly id: number; readonly request: ChartRequest };

export type FromWorker =
  | { readonly type: 'loaded'; readonly id: number }
  /** The packages are loaded and the tests or the chart have begun: the time limit starts now. */
  | { readonly type: 'started'; readonly id: number }
  | { readonly type: 'result'; readonly id: number; readonly result: RunResult }
  | { readonly type: 'drawn'; readonly id: number; readonly result: ChartResult }
  /** Pyodide or a package didn't load. With no id, the worker itself couldn't start. */
  | { readonly type: 'failed'; readonly id: number | null; readonly message: string };
