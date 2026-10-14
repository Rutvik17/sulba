import { expect, test } from 'vitest';
import { stopwatch, type View } from './stopwatch';

function setup(visible = true) {
  let time = 0;
  let shown = visible;
  const listeners = new Set<() => void>();
  const view: View = {
    visible: () => shown,
    onChange: (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
  const watch = stopwatch(view, () => time);
  return {
    watch,
    listeners,
    wait: (seconds: number) => {
      time += seconds * 1000;
    },
    show: (now: boolean) => {
      shown = now;
      for (const listener of listeners) listener();
    },
  };
}

test('each lap is the time since the one before', () => {
  const { watch, wait } = setup();
  wait(30);
  expect(watch.lap()).toBe(30);
  wait(12.4);
  expect(watch.lap()).toBe(12);
});

test('time while the page is out of view does not count', () => {
  const { watch, wait, show } = setup();
  wait(10);
  show(false);
  wait(600);
  show(true);
  wait(5);
  expect(watch.lap()).toBe(15);
});

test('a page opened out of view starts counting when it comes into view', () => {
  const { watch, wait, show } = setup(false);
  wait(100);
  show(true);
  wait(20);
  expect(watch.lap()).toBe(20);
});

test('stopping it stops listening', () => {
  const { watch, listeners } = setup();
  watch.stop();
  expect(listeners.size).toBe(0);
});
