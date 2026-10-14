import { describe, expect, it } from 'vitest';
import { attemptOf, localDay, maxSeconds, Outbox } from './outbox.ts';

const stage = { id: 'stg_aaaaaa', version: '0123456789abcdef' };
const at = new Date(2026, 9, 14, 23, 30);

function memory(): Pick<Storage, 'getItem' | 'setItem' | 'removeItem'> & {
  map: Map<string, string>;
} {
  const map = new Map<string, string>();
  return {
    map,
    getItem: (key) => map.get(key) ?? null,
    setItem: (key, value) => void map.set(key, value),
    removeItem: (key) => void map.delete(key),
  };
}

describe('attemptOf', () => {
  it('records a run with its tests and checks', () => {
    const attempt = attemptOf(
      stage,
      { kind: 'run', tests: { passed: 4, total: 6 }, checks: { passed: 1, total: 2 } },
      95.4,
      at,
      'id-1',
    );
    expect(attempt).toEqual({
      id: 'id-1',
      stage_id: 'stg_aaaaaa',
      stage_version: '0123456789abcdef',
      kind: 'run',
      tests_passed: 4,
      tests_total: 6,
      checks_passed: 1,
      checks_total: 2,
      hint: null,
      caught: null,
      problems: null,
      seconds: 95,
      happened_at: at.toISOString(),
      day: '2026-10-14',
    });
  });

  it('records a Catch stage pass with its review', () => {
    const attempt = attemptOf(
      stage,
      { kind: 'pass', review: { caught: ['tst_aaaaaa'], problems: 3 } },
      0,
      at,
    );
    expect(attempt).toMatchObject({ kind: 'pass', caught: ['tst_aaaaaa'], problems: 3 });
    expect(attempt.tests_total).toBeNull();
  });

  it('keeps the time within what one attempt can carry', () => {
    expect(attemptOf(stage, { kind: 'solution' }, 9000, at).seconds).toBe(maxSeconds);
    expect(attemptOf(stage, { kind: 'hint', hint: 1 }, -3, at).seconds).toBe(0);
  });
});

describe('localDay', () => {
  it('is the day where the learner is', () => {
    expect(localDay(new Date(2026, 0, 5, 0, 1))).toBe('2026-01-05');
  });
});

describe('Outbox', () => {
  it('keeps attempts until they are removed', () => {
    const storage = memory();
    const outbox = new Outbox(storage);
    const first = attemptOf(stage, { kind: 'solution' }, 1, at);
    const second = attemptOf(stage, { kind: 'hint', hint: 2 }, 1, at);
    outbox.add(first);
    outbox.add(second);
    expect(new Outbox(storage).all()).toEqual([first, second]);

    outbox.remove(new Set([first.id]));
    expect(outbox.all()).toEqual([second]);
    outbox.remove(new Set([second.id]));
    expect(storage.map.size).toBe(0);
  });

  it('starts empty when what it kept can no longer be read', () => {
    const storage = memory();
    storage.setItem('sulba:outbox', '{not json');
    expect(new Outbox(storage).all()).toEqual([]);
    storage.setItem('sulba:outbox', JSON.stringify([{ id: 1 }, 'x']));
    expect(new Outbox(storage).all()).toEqual([]);
  });

  it('goes on when storage is blocked', () => {
    const blocked = {
      getItem: () => {
        throw new Error('blocked');
      },
      setItem: () => {
        throw new Error('blocked');
      },
      removeItem: () => {
        throw new Error('blocked');
      },
    };
    const outbox = new Outbox(blocked);
    expect(() => outbox.add(attemptOf(stage, { kind: 'solution' }, 1, at))).not.toThrow();
    expect(outbox.all()).toEqual([]);
  });
});
