import { expect, test } from 'vitest';
import { latestOnly } from './latest';

/** A task that finishes when the test says so. */
function task() {
  const started: number[] = [];
  const finishers: (() => void)[] = [];
  const run = (request: number) =>
    new Promise<number>((resolve) => {
      started.push(request);
      finishers.push(() => resolve(request * 10));
    });
  const finish = async () => {
    finishers.shift()?.();
    await new Promise((resolve) => setTimeout(resolve, 0));
  };
  return { started, run, finish };
}

test('requests made while one runs leave only the latest waiting', async () => {
  const { started, run, finish } = task();
  const done: [number, number][] = [];
  const ask = latestOnly(run, (request, result) => done.push([request, result]));

  ask(1);
  ask(2);
  ask(3);
  expect(started).toEqual([1]);
  await finish();
  expect(started).toEqual([1, 3]);
  await finish();
  expect(done).toEqual([
    [1, 10],
    [3, 30],
  ]);
});

test('a request after the last one finished runs at once', async () => {
  const { started, run, finish } = task();
  const ask = latestOnly(run, () => {});

  ask(1);
  await finish();
  ask(2);
  expect(started).toEqual([1, 2]);
});
