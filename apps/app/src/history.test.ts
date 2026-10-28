import type { Change } from '@sulba/data/specs';
import { describe, expect, test } from 'vitest';
import { ago } from './format';
import { type Context, whatOf, whoOf } from './history';

const context: Context = {
  spec: 12,
  names: new Map([['b', 'Ben Ortiz']]),
  criteria: new Map([['c3', 3]]),
};

function change(partial: Partial<Change>): Change {
  return {
    id: 1,
    at: '2026-10-27T12:00:00Z',
    actorKind: 'person',
    actorName: 'Ada Lovelace',
    action: 'spec.updated',
    subjectType: 'spec',
    subjectId: 's',
    changes: {},
    ...partial,
  };
}

describe('whatOf', () => {
  test('says what changed about a spec, in one sentence', () => {
    expect(whatOf(change({ action: 'spec.created' }), context)).toBe('wrote the spec');
    expect(
      whatOf(
        change({
          changes: { status: ['draft', 'in_review'], title: ['Retry', 'Retry a payment'] },
        }),
        context,
      ),
    ).toBe('renamed it “Retry a payment” and moved it to In review');
    expect(whatOf(change({ changes: { body: null } }), context)).toBe('edited its text');
    expect(whatOf(change({ changes: { owner_id: [null, 'b'] } }), context)).toBe(
      'gave it to Ben Ortiz',
    );
    expect(whatOf(change({ changes: { owner_id: ['b', null] } }), context)).toBe(
      'left it without an owner',
    );
  });

  test('names each criterion by its ID, even once it is gone', () => {
    const criterion = { subjectType: 'criterion', subjectId: 'c3' } as const;
    expect(
      whatOf(
        change({ ...criterion, action: 'criterion.created', changes: { number: [null, 3] } }),
        context,
      ),
    ).toBe('added SPEC-12/AC-3');
    expect(
      whatOf(
        change({ ...criterion, action: 'criterion.updated', changes: { text: ['a', 'b'] } }),
        context,
      ),
    ).toBe('reworded SPEC-12/AC-3');
    expect(
      whatOf(
        change({
          subjectType: 'criterion',
          subjectId: 'gone',
          action: 'criterion.deleted',
          changes: { number: [4, null] },
        }),
        context,
      ),
    ).toBe('removed SPEC-12/AC-4');
  });

  test('says when a reworded criterion’s tests are confirmed', () => {
    const criterion = { subjectType: 'criterion', subjectId: 'c3' } as const;
    expect(
      whatOf(
        change({
          ...criterion,
          action: 'criterion.updated',
          changes: { text: ['a', 'b'], suspect_since: [null, '2026-10-28T09:00:00Z'] },
        }),
        context,
      ),
    ).toBe('reworded SPEC-12/AC-3');
    expect(
      whatOf(
        change({
          ...criterion,
          action: 'criterion.updated',
          changes: { suspect_since: ['2026-10-28T09:00:00Z', null] },
        }),
        context,
      ),
    ).toBe('confirmed that SPEC-12/AC-3’s tests check its wording');
  });
});

describe('whoOf', () => {
  test('names people, marks agents and says when someone has left', () => {
    expect(whoOf(change({}))).toBe('Ada Lovelace');
    expect(whoOf(change({ actorKind: 'agent' }))).toBe('Ada Lovelace’s agent');
    expect(whoOf(change({ actorName: null }))).toBe('Someone who has left');
  });
});

describe('ago', () => {
  const now = Date.parse('2026-10-27T12:00:00Z');
  test('says how long ago, and past four weeks the day', () => {
    expect(ago('2026-10-27T11:59:30Z', now)).toBe('just now');
    expect(ago('2026-10-27T11:55:00Z', now)).toBe('5 minutes ago');
    expect(ago('2026-10-27T09:00:00Z', now)).toBe('3 hours ago');
    expect(ago('2026-10-26T11:00:00Z', now)).toBe('yesterday');
    expect(ago('2026-09-01T12:00:00Z', now)).toMatch(/2026/);
  });
});
