import type { Change } from '@sulba/data/specs';
import { describe, expect, test } from 'vitest';
import { type Context, whatOf, whoOf } from './history';

const context: Context = {
  spec: 12,
  names: new Map([['b', 'Ben Ortiz']]),
  criteria: new Map([['c3', 3]]),
  reviewers: new Map([['r1', 'b']]),
  tasks: new Map([['t7', 7]]),
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
  test('says who was asked to review the spec, and what each reviewer answered', () => {
    const review = (partial: Partial<Change>) =>
      change({ subjectType: 'review', subjectId: 'r1', ...partial });
    expect(
      whatOf(review({ action: 'review.created', changes: { reviewer_id: [null, 'b'] } }), context),
    ).toBe('asked Ben Ortiz to review it');
    expect(
      whatOf(
        review({ action: 'review.updated', changes: { verdict: ['pending', 'approved'] } }),
        context,
      ),
    ).toBe('approved it');
    expect(
      whatOf(
        review({
          action: 'review.updated',
          changes: { verdict: ['pending', 'changes_requested'], note: [null, 'Say how long'] },
        }),
        context,
      ),
    ).toBe('asked for changes');
    expect(
      whatOf(
        review({ action: 'review.updated', changes: { verdict: ['approved', 'pending'] } }),
        context,
      ),
    ).toBe('asked Ben Ortiz to review it again');
    expect(
      whatOf(review({ action: 'review.deleted', changes: { reviewer_id: ['b', null] } }), context),
    ).toBe('took Ben Ortiz off its reviewers');
    expect(
      whatOf(
        review({
          action: 'review.deleted',
          subjectId: 'r9',
          changes: { reviewer_id: ['x', null] },
        }),
        context,
      ),
    ).toBe('took someone who has left off its reviewers');
  });

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

describe('whatOf for tasks', () => {
  const task = (partial: Partial<Change>) =>
    change({ subjectType: 'task', subjectId: 't7', action: 'task.updated', ...partial });
  const moved = (from: string, to: string) =>
    whatOf(task({ changes: { status: [from, to] } }), context);

  test('says who wrote, took, blocked and handed in a task', () => {
    expect(whatOf(task({ action: 'task.created', changes: { number: [null, 7] } }), context)).toBe(
      'wrote TASK-7',
    );
    expect(moved('open', 'in_progress')).toBe('took TASK-7');
    expect(moved('in_progress', 'blocked')).toBe('blocked TASK-7');
    expect(moved('blocked', 'in_progress')).toBe('resumed TASK-7');
    expect(moved('in_progress', 'in_review')).toBe('handed in TASK-7');
    expect(moved('in_review', 'in_progress')).toBe('sent TASK-7 back');
  });

  test('says who finished, canceled, released or opened a task again', () => {
    expect(moved('in_review', 'done')).toBe('marked TASK-7 done');
    expect(moved('open', 'canceled')).toBe('canceled TASK-7');
    expect(moved('in_progress', 'open')).toBe('released TASK-7');
    expect(moved('done', 'open')).toBe('opened TASK-7 again');
  });

  test('says what was edited', () => {
    expect(
      whatOf(
        task({
          changes: { title: ['Build it', 'Build the API'], role: ['build', 'test'], body: null },
        }),
        context,
      ),
    ).toBe(
      'renamed TASK-7 “Build the API”, made TASK-7 a Test task and edited TASK-7’s instructions',
    );
  });
});

describe('whoOf', () => {
  test('names people, marks agents and says when someone has left', () => {
    expect(whoOf(change({}))).toBe('Ada Lovelace');
    expect(whoOf(change({ actorKind: 'agent' }))).toBe('Ada Lovelace’s agent');
    expect(whoOf(change({ actorName: null }))).toBe('Someone who has left');
  });
});
