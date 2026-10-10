import { describe, expect, test } from 'vitest';
import {
  at,
  columnMeans,
  columnStds,
  draftStandardize,
  FIX,
  failure,
  finished,
  fixedStandardize,
  frameAt,
  LOOP,
  matrix,
} from './session-clip';

describe('the clip shows real numbers', () => {
  // NumPy 2.5.3 on the same matrix, 9 October 2026:
  //   (X - X.mean()) / X.std()             column means [-0.8405, 0.8405], stds [0.0762, 0.7625]
  //   (X - X.mean(axis=0)) / X.std(axis=0) column means [0, 0], stds [1, 1]
  test('the assistant draft matches NumPy to 4 decimal places', () => {
    const draft = draftStandardize(matrix);

    columnMeans(draft).forEach((m, j) => {
      expect(m).toBeCloseTo([-0.8405, 0.8405][j] ?? Number.NaN, 4);
    });
    columnStds(draft).forEach((s, j) => {
      expect(s).toBeCloseTo([0.0762, 0.7625][j] ?? Number.NaN, 4);
    });
  });

  test('the fix gives every column mean 0 and standard deviation 1', () => {
    const fixed = fixedStandardize(matrix);

    for (const m of columnMeans(fixed)) expect(m).toBeCloseTo(0, 12);
    for (const s of columnStds(fixed)) expect(s).toBeCloseTo(1, 12);
  });

  test('the failing test shows its input and the means it got', () => {
    expect(failure.input).toBe('X = [[1, 10], [2, 20], [3, 30]]');
    expect(failure.message).toBe('Column means are [-0.84, 0.84], expected [0, 0]');
  });
});

describe('the session plays in order', () => {
  test('nothing has run at the start', () => {
    const frame = frameAt(0);

    expect(frame.tests).toEqual(['idle', 'idle', 'idle', 'idle']);
    expect(frame.summary).toBe('idle');
    expect(frame.typedA + frame.typedB).toBe(0);
  });

  test('the first run fails the two column tests', () => {
    const frame = frameAt(at.failed + 100);

    expect(frame.tests).toEqual(['pass', 'fail', 'fail', 'pass']);
    expect(frame.summary).toBe('fail');
    expect(frame.failNote).toBe(true);
  });

  test('axis=0 is typed into the mean, then into the standard deviation', () => {
    expect(frameAt(at.typeA + 2 * 75).typedA).toBe(3);
    expect(frameAt(at.typeB - 1)).toMatchObject({ typedA: FIX.length, typedB: 0 });
    expect(frameAt(at.press2)).toMatchObject({ typedA: FIX.length, typedB: FIX.length });
  });

  test('the second run passes every test and the session is done', () => {
    const frame = frameAt(at.done + 100);

    expect(frame.tests).toEqual(['pass', 'pass', 'pass', 'pass']);
    expect(frame.summary).toBe('pass');
    expect(frame.failNote).toBe(false);
    expect(frame.done).toBe(true);
  });

  test('the finished frame shown for reduced motion has every test passed', () => {
    expect(frameAt(finished)).toMatchObject({ summary: 'pass', done: true, hidden: false });
  });

  test('the loop resets behind a fade and starts again from nothing', () => {
    expect(frameAt(at.fadeOut).hidden).toBe(true);
    expect(frameAt(at.reset)).toMatchObject({
      summary: 'idle',
      typedA: 0,
      done: false,
      hidden: true,
    });
    expect(frameAt(LOOP - 1)).toMatchObject({ summary: 'idle', hidden: false });
  });
});

describe('the pointer behaves like a real one', () => {
  test('it hides while text is typed and comes back when it moves on', () => {
    expect(frameAt(at.typeA + 100).away).toBe(true);
    expect(frameAt(at.typeB + 100).away).toBe(true);
    expect(frameAt(at.typeB - 600).away).toBe(false);
    expect(frameAt(at.press2).away).toBe(false);
  });

  test('it presses Run tests twice', () => {
    expect(frameAt(at.press1 + 60)).toMatchObject({ down: true, press: true });
    expect(frameAt(at.press2 + 60)).toMatchObject({ down: true, press: true });
    expect(frameAt(at.press1 + 200).down).toBe(false);
  });

  test('it travels from the tests to the code and back', () => {
    expect(frameAt(at.press1).pointer).toMatchObject({ to: 'run', k: 1 });
    expect(frameAt(at.typeA).pointer).toMatchObject({ from: 'run', to: 'a', k: 1 });
    expect(frameAt(at.typeB).pointer).toMatchObject({ to: 'b', k: 1 });
    expect(frameAt(at.press2).pointer).toMatchObject({ to: 'run', k: 1 });
  });

  test('after typing it comes back where the typing ended', () => {
    const backAfterA = frameAt(at.typeA + 700);
    const backAfterB = frameAt(at.typeB + 700);

    expect(backAfterA).toMatchObject({ away: false, pointer: { from: 'a-end', to: 'b' } });
    expect(backAfterB).toMatchObject({ away: false, pointer: { from: 'b-end', to: 'run' } });
  });
});
