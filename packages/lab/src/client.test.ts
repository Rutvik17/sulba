import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { Lab, LabLoadError, type WorkerLike } from './client.ts';
import type { FromWorker, ToWorker } from './messages.ts';
import type { ChartRequest, ChartResult, RunRequest, RunResult } from './protocol.ts';

class StandIn implements WorkerLike {
  readonly sent: ToWorker[] = [];
  terminated = false;
  readonly #messages: ((event: MessageEvent<FromWorker>) => void)[] = [];
  readonly #errors: ((event: ErrorEvent) => void)[] = [];

  postMessage(message: ToWorker) {
    this.sent.push(message);
  }

  addEventListener(type: 'message', listener: (event: MessageEvent<FromWorker>) => void): void;
  addEventListener(type: 'error', listener: (event: ErrorEvent) => void): void;
  addEventListener(
    type: 'message' | 'error',
    listener: ((event: MessageEvent<FromWorker>) => void) | ((event: ErrorEvent) => void),
  ) {
    if (type === 'message')
      this.#messages.push(listener as (event: MessageEvent<FromWorker>) => void);
    else this.#errors.push(listener as (event: ErrorEvent) => void);
  }

  terminate() {
    this.terminated = true;
  }

  reply(data: FromWorker) {
    for (const listener of this.#messages) listener({ data } as MessageEvent<FromWorker>);
  }

  crash(message: string) {
    for (const listener of this.#errors) listener({ message } as ErrorEvent);
  }

  /** The id of the last task sent. */
  get id(): number {
    const last = this.sent.at(-1);
    if (!last || last.type === 'start') throw new Error('No task was sent.');
    return last.id;
  }
}

const request: RunRequest = {
  files: { 'model.py': '' },
  tests: ['tests/test_model.py'],
  packages: [],
};
const passed: RunResult = { status: 'pass', tests: [], problem: null, output: '', durationMs: 3 };
const chartRequest: ChartRequest = {
  files: { 'model.py': '', 'chart.py': '' },
  values: { w: 1 },
  packages: ['numpy'],
};
const drawn: ChartResult = {
  chart: {
    x: { min: 0, max: 1, step: 1, label: 'x' },
    y: { min: 0, max: 1, step: 1, label: 'y' },
    lines: [{ style: 'main', label: 'A line', x: [0, 1], y: [0, null] }],
    points: [],
    readouts: [],
    description: 'A line',
  },
  problem: null,
};

let workers: StandIn[];
let lab: Lab;

beforeEach(() => {
  vi.useFakeTimers();
  workers = [];
  lab = new Lab({
    indexURL: '/pyodide/',
    createWorker: () => {
      const worker = new StandIn();
      workers.push(worker);
      return worker;
    },
  });
});

afterEach(() => {
  vi.useRealTimers();
});

const settle = () => vi.advanceTimersByTimeAsync(0);

function worker(index: number): StandIn {
  const found = workers[index];
  if (!found) throw new Error(`No worker ${index}.`);
  return found;
}

test('a run starts the worker, sends the request and gives back its result', async () => {
  const result = lab.run(request);
  await settle();
  expect(worker(0).sent).toEqual([
    { type: 'start', indexURL: '/pyodide/' },
    { type: 'run', id: 0, request },
  ]);
  worker(0).reply({ type: 'started', id: 0 });
  worker(0).reply({ type: 'result', id: 0, result: passed });
  await expect(result).resolves.toEqual(passed);
});

test('a chart is sent like a run and gives back what it drew', async () => {
  const result = lab.chart(chartRequest);
  await settle();
  expect(worker(0).sent.at(-1)).toEqual({ type: 'chart', id: 0, request: chartRequest });
  worker(0).reply({ type: 'started', id: 0 });
  worker(0).reply({ type: 'drawn', id: 0, result: drawn });
  await expect(result).resolves.toEqual(drawn);
});

test('a chart past the time limit is stopped, like a run', async () => {
  const result = lab.chart(chartRequest);
  await settle();
  worker(0).reply({ type: 'started', id: 0 });
  await vi.advanceTimersByTimeAsync(5000);
  await expect(result).resolves.toEqual({
    chart: null,
    problem: { kind: 'TimeLimit', message: 'Stopped after 5 seconds.' },
  });
  expect(worker(0).terminated).toBe(true);
});

test('runs go one at a time, in order', async () => {
  const first = lab.run(request);
  const second = lab.run(request);
  await settle();
  expect(worker(0).sent.filter((message) => message.type === 'run')).toHaveLength(1);
  worker(0).reply({ type: 'result', id: 0, result: passed });
  await first;
  await settle();
  expect(worker(0).id).toBe(1);
  worker(0).reply({ type: 'result', id: 1, result: { ...passed, durationMs: 4 } });
  await expect(second).resolves.toMatchObject({ durationMs: 4 });
  expect(workers).toHaveLength(1);
});

test('a run past the time limit is stopped, and the next run gets a new worker', async () => {
  const result = lab.run(request);
  await settle();
  worker(0).reply({ type: 'started', id: 0 });
  await vi.advanceTimersByTimeAsync(5000);
  await expect(result).resolves.toEqual({
    status: 'error',
    tests: [],
    problem: { kind: 'TimeLimit', message: 'Stopped after 5 seconds.', location: null },
    output: '',
    durationMs: 5000,
  });
  expect(worker(0).terminated).toBe(true);

  const next = lab.run(request);
  await settle();
  expect(worker(1).sent[0]).toEqual({ type: 'start', indexURL: '/pyodide/' });
  worker(1).reply({ type: 'result', id: worker(1).id, result: passed });
  await expect(next).resolves.toEqual(passed);
});

test('loading Python and packages is not counted against the time limit', async () => {
  const result = lab.run(request);
  await settle();
  await vi.advanceTimersByTimeAsync(20_000);
  worker(0).reply({ type: 'started', id: 0 });
  await vi.advanceTimersByTimeAsync(4000);
  worker(0).reply({ type: 'result', id: 0, result: passed });
  await expect(result).resolves.toEqual(passed);
  expect(worker(0).terminated).toBe(false);
});

test('a result from a stopped worker is ignored', async () => {
  const result = lab.run(request);
  await settle();
  worker(0).reply({ type: 'started', id: 0 });
  await vi.advanceTimersByTimeAsync(5000);
  worker(0).reply({ type: 'result', id: 0, result: passed });
  await expect(result).resolves.toMatchObject({ problem: { kind: 'TimeLimit' } });
});

test('a worker that cannot load Python fails its task, and the next task starts afresh', async () => {
  const result = lab.run(request);
  await settle();
  worker(0).reply({ type: 'failed', id: null, message: 'Network error' });
  await expect(result).rejects.toEqual(new LabLoadError('Network error'));
  expect(worker(0).terminated).toBe(true);

  const prepared = lab.prepare(['numpy']);
  await settle();
  expect(worker(1).sent).toEqual([
    { type: 'start', indexURL: '/pyodide/' },
    { type: 'load', id: 1, packages: ['numpy'] },
  ]);
  worker(1).reply({ type: 'loaded', id: 1 });
  await expect(prepared).resolves.toBeUndefined();
});

test('a package that fails to load fails only its task', async () => {
  const prepared = lab.prepare(['numpy']);
  await settle();
  worker(0).reply({ type: 'failed', id: 0, message: 'numpy did not load' });
  await expect(prepared).rejects.toBeInstanceOf(LabLoadError);
  expect(worker(0).terminated).toBe(false);
});

test('a worker that crashes fails its task', async () => {
  const result = lab.run(request);
  await settle();
  worker(0).crash('Script error');
  await expect(result).rejects.toEqual(new LabLoadError('Script error'));
  expect(worker(0).terminated).toBe(true);
});
