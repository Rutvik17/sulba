// The page's side of the lab. It sends the worker one task at a time, stops a run or a chart that
// passes the time limit by ending the worker, and starts a new worker for the next task.
import type { FromWorker, ToWorker } from './messages.ts';
import {
  type ChartRequest,
  type ChartResult,
  type Problem,
  type RunRequest,
  type RunResult,
  timeLimitMs,
} from './protocol.ts';

/** The parts of a Worker the lab uses, so tests can stand in for one. */
export interface WorkerLike {
  postMessage(message: ToWorker): void;
  addEventListener(type: 'message', listener: (event: MessageEvent<FromWorker>) => void): void;
  addEventListener(type: 'error', listener: (event: ErrorEvent) => void): void;
  terminate(): void;
}

export interface LabOptions {
  /** The folder Sulba serves Pyodide from, ending in a slash. */
  readonly indexURL: string;
  readonly timeLimitMs?: number;
  readonly createWorker?: () => WorkerLike;
}

/** Python or a package couldn't be loaded, usually because the connection dropped. */
export class LabLoadError extends Error {
  override readonly name = 'LabLoadError';
}

interface Finish<T> {
  resolve(value: T): void;
  reject(error: LabLoadError): void;
}

interface Task {
  readonly id: number;
  readonly handle: (message: FromWorker) => void;
  readonly reject: (error: LabLoadError) => void;
}

function createModuleWorker(): WorkerLike {
  return new Worker(new URL('./worker.ts', import.meta.url), { type: 'module' });
}

export class Lab {
  readonly #indexURL: string;
  readonly #timeLimitMs: number;
  readonly #createWorker: () => WorkerLike;
  #worker: WorkerLike | null = null;
  #task: Task | null = null;
  #queue: Promise<unknown> = Promise.resolve();
  #next = 0;

  constructor(options: LabOptions) {
    this.#indexURL = options.indexURL;
    this.#timeLimitMs = options.timeLimitMs ?? timeLimitMs;
    this.#createWorker = options.createWorker ?? createModuleWorker;
  }

  /** Load Python and these packages ahead of the first run. */
  prepare(packages: RunRequest['packages']): Promise<void> {
    return this.#enqueue<void>(
      (id) => ({ type: 'load', id, packages }),
      (message, finish) => {
        if (message.type === 'loaded') finish.resolve();
      },
    );
  }

  run(request: RunRequest): Promise<RunResult> {
    return this.#timed(
      (id) => ({ type: 'run', id, request }),
      (reply) => (reply.type === 'result' ? reply.result : null),
      (problem) => ({
        status: 'error',
        tests: [],
        problem: { ...problem, location: null },
        output: '',
        durationMs: this.#timeLimitMs,
      }),
    );
  }

  /** What a stage's chart.py draws with these values. */
  chart(request: ChartRequest): Promise<ChartResult> {
    return this.#timed(
      (id) => ({ type: 'chart', id, request }),
      (reply) => (reply.type === 'drawn' ? reply.result : null),
      (problem) => ({ chart: null, problem }),
    );
  }

  /** End the worker. A later task starts a new one. */
  dispose() {
    this.#end();
  }

  /**
   * A task the time limit applies to, from when the worker starts it: past the limit, the worker is
   * ended and the task gives what `stopped` makes of the problem.
   */
  #timed<T>(
    message: (id: number) => ToWorker,
    answer: (reply: FromWorker) => T | null,
    stopped: (problem: Pick<Problem, 'kind' | 'message'>) => T,
  ): Promise<T> {
    let timer: ReturnType<typeof setTimeout> | undefined;
    return this.#enqueue<T>(message, (reply, finish) => {
      if (reply.type === 'started') {
        timer = setTimeout(() => {
          this.#end();
          const seconds = this.#timeLimitMs / 1000;
          finish.resolve(
            stopped({ kind: 'TimeLimit', message: `Stopped after ${seconds} seconds.` }),
          );
        }, this.#timeLimitMs);
      }
      const value = answer(reply);
      if (value !== null) finish.resolve(value);
    }).finally(() => clearTimeout(timer));
  }

  #enqueue<T>(
    message: (id: number) => ToWorker,
    handle: (message: FromWorker, finish: Finish<T>) => void,
  ): Promise<T> {
    const task = this.#queue.then(
      () =>
        new Promise<T>((resolve, reject) => {
          const id = this.#next++;
          const finish: Finish<T> = {
            resolve: (value) => {
              this.#task = null;
              resolve(value);
            },
            reject: (error) => {
              this.#task = null;
              reject(error);
            },
          };
          this.#task = {
            id,
            handle: (reply) =>
              reply.type === 'failed'
                ? finish.reject(new LabLoadError(reply.message))
                : handle(reply, finish),
            reject: finish.reject,
          };
          this.#connect().postMessage(message(id));
        }),
    );
    this.#queue = task.catch(() => {});
    return task;
  }

  #connect(): WorkerLike {
    if (this.#worker) return this.#worker;
    const worker = this.#createWorker();
    worker.addEventListener('message', ({ data }) => {
      if (worker !== this.#worker) return;
      if (data.type === 'failed' && data.id === null) return this.#broken(data.message);
      if (data.id === this.#task?.id) this.#task.handle(data);
    });
    worker.addEventListener('error', (event) => {
      if (worker === this.#worker) this.#broken(event.message);
    });
    worker.postMessage({ type: 'start', indexURL: this.#indexURL });
    this.#worker = worker;
    return worker;
  }

  /** The worker can't go on: end it, and fail the task it had. */
  #broken(message: string) {
    this.#end();
    this.#task?.reject(new LabLoadError(message));
  }

  #end() {
    this.#worker?.terminate();
    this.#worker = null;
  }
}
