import { describe, expect, test } from 'vitest';
import {
  build,
  buildAt,
  catchAt,
  catchStage,
  lineText,
  ship,
  shipAt,
  stageAt,
  stageStart,
  stages,
  typedLength,
} from './lab-scroll';

const code = (lines: readonly { indent: number; runs: readonly { text: string }[] }[]) =>
  lines.map((line) => lineText({ indent: line.indent, runs: line.runs })).join('\n');

describe('the scroll position picks the stage', () => {
  test('a third of the track per stage, from Build to Ship', () => {
    expect(stages.map((stage) => stage.name)).toEqual(['Build', 'Catch', 'Ship']);
    expect(stageAt(0)).toEqual({ stage: 0, local: 0 });
    expect(stageAt(0.5)).toEqual({ stage: 1, local: 0.5 });
    expect(stageAt(1)).toEqual({ stage: 2, local: 1 });
  });

  test('scrolling past either end holds the first or the last frame', () => {
    expect(stageAt(-0.4)).toEqual({ stage: 0, local: 0 });
    expect(stageAt(1.7)).toEqual({ stage: 2, local: 1 });
  });

  test('a stage name leads to the start of its stage', () => {
    stages.forEach((_, i) => {
      expect(stageAt(stageStart(i)).stage).toBe(i);
      expect(stageAt(stageStart(i)).local).toBeLessThan(0.1);
    });
  });
});

describe('Build types the sigmoid, then its tests pass', () => {
  test('nothing is typed or run at the start', () => {
    expect(buildAt(0)).toEqual({ typed: 0, tests: ['idle', 'idle', 'idle', 'idle'], done: false });
  });

  test('typing only moves forward as the scroll does', () => {
    const typed = [0.1, 0.2, 0.3, 0.4, 0.5].map((local) => buildAt(local).typed);
    expect(typed).toEqual([...typed].sort((a, b) => a - b));
    expect(new Set(typed).size).toBe(typed.length);
  });

  test('by the end every character is typed and all four tests pass', () => {
    expect(buildAt(1)).toEqual({
      typed: typedLength(build.body),
      tests: ['pass', 'pass', 'pass', 'pass'],
      done: true,
    });
  });

  test('the code is the lab reference sigmoid, which never overflows', () => {
    expect(code(build.body)).toBe(
      [
        '    z = np.asarray(z, dtype=float)',
        '    out = np.empty_like(z)',
        '    positive = z >= 0',
        '    out[positive] = 1.0 / (1.0 + np.exp(-z[positive]))',
        '    ez = np.exp(z[~positive])',
        '    out[~positive] = ez / (1.0 + ez)',
        '    return out',
      ].join('\n'),
    );
  });
});

describe("Catch fixes one of the assistant's mistakes", () => {
  test("the assistant's tests pass and no production check does, before the fix", () => {
    const frame = catchAt(0.3);
    expect(frame.tests).toEqual(['pass', 'pass', 'pass']);
    expect(frame.checks).toBe('none');
    expect(frame.removed).toBe(false);
  });

  test('"fit_" is selected, then deleted', () => {
    expect(catchAt(0.42).selected).toBeGreaterThan(0);
    expect(catchAt(0.5).selected).toBe(catchStage.removed.length);
    expect(catchAt(0.6)).toMatchObject({ selected: 0, removed: true });
  });

  test('after the fix one more production check passes', () => {
    expect(catchAt(1)).toMatchObject({ checks: 'one', tests: ['pass', 'pass', 'pass'] });
    expect(catchStage.checks).toBe(5);
  });

  test('the fix turns fit_transform into transform, so new samples get the training numbers', () => {
    expect(`${catchStage.before}${catchStage.removed}${catchStage.after}`).toBe(
      '    X_new = self.scaler.fit_transform(self.imputer.transform(X_new))',
    );
    expect(`${catchStage.before}${catchStage.after}`).toBe(
      '    X_new = self.scaler.transform(self.imputer.transform(X_new))',
    );
  });
});

describe('Ship rewrites a slow search until the code is ready', () => {
  test('the hidden tests pass but the speed check fails at first', () => {
    expect(shipAt(0.3)).toMatchObject({ hidden: 'pass', checks: ['fail', 'pass'], removed: false });
  });

  test('the slow loop is selected, removed, and the new body typed', () => {
    expect(shipAt(0.35)).toMatchObject({ selected: true, removed: false });
    expect(shipAt(0.5)).toMatchObject({ selected: false, removed: true });
    expect(shipAt(0.5).typed).toBeGreaterThan(0);
    expect(shipAt(0.76).typed).toBe(typedLength(ship.fast));
  });

  test('by the end both checks pass and it is ready to ship', () => {
    expect(shipAt(1)).toMatchObject({ hidden: 'pass', checks: ['pass', 'pass'], ready: true });
  });

  test('the slow search tries every value; the fast one sorts the positives once', () => {
    expect(code(ship.slow)).toBe(
      [
        '    for t in np.sort(np.unique(p))[::-1]:',
        '        if np.mean(p[y == 1] >= t) >= min_recall:',
        '            return float(t)',
      ].join('\n'),
    );
    expect(code(ship.fast)).toBe(
      [
        '    positives = np.sort(p[y == 1])[::-1]',
        '    needed = max(1, int(np.ceil(min_recall * len(positives) - 1e-9)))',
        '    return float(positives[needed - 1])',
      ].join('\n'),
    );
  });
});
