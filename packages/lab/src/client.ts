// The page's side of the lab. It sends the worker one task at a time, stops a run that passes
// the time limit by ending the worker, and starts a new worker for the next task.
import type { FromWorker, ToWorker } from './messages.ts';
import { type RunRequest, type RunResult, timeLimitMs } from './protocol.ts';

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
    let timer: ReturnType<typeof setTimeout> | undefined;
    return this.#enqueue<RunResult>(
      (id) => ({ type: 'run', id, request }),
      (message, finish) => {
        if (message.type === 'started') {
          timer = setTimeout(() => {
            this.#end();
            finish.resolve(this.#stopped());
          }, this.#timeLimitMs);
        }
        if (message.type === 'result') finish.resolve(message.result);
      },
    ).finally(() => clearTimeout(timer));
  }

  /** End the worker. A later task starts a new one. */
  dispose() {
    this.#end();
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

  #stopped(): RunResult {
    const seconds = this.#timeLimitMs / 1000;
    return {
      status: 'error',
      tests: [],
      problem: { kind: 'TimeLimit', message: `Stopped after ${seconds} seconds.`, location: null },
      output: '',
      durationMs: this.#timeLimitMs,
    };
  }
}
