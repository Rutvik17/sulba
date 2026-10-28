import { describe, expect, it, vi } from 'vitest';
import type { Client } from './client.ts';
import { answerProblem, reviewSpec, standingOf } from './reviewers.ts';

describe('standingOf', () => {
  it('counts the approvals, and the requests for changes when there are any', () => {
    expect(standingOf([])).toBe('No reviewers');
    expect(standingOf([{ verdict: 'approved' }, { verdict: 'pending' }])).toBe('1 of 2 approved');
    expect(
      standingOf([
        { verdict: 'approved' },
        { verdict: 'changes_requested' },
        { verdict: 'pending' },
      ]),
    ).toBe('1 of 3 approved, 1 asked for changes');
  });
});

describe('answerProblem', () => {
  it('asks a request for changes to say what to change', () => {
    expect(answerProblem('changes_requested', '  ')).toBe('Say what to change.');
    expect(answerProblem('changes_requested', 'Say how long it waits')).toBeNull();
    expect(answerProblem('approved', '')).toBeNull();
  });

  it('keeps a note within what Postgres takes', () => {
    expect(answerProblem('approved', 'x'.repeat(2001))).toBe(
      'A note has at most 2,000 characters.',
    );
  });
});

describe('reviewSpec', () => {
  it('sends the trimmed note, or none, and gives the spec’s status', async () => {
    const rpc = vi.fn(async () => ({ data: 'approved', error: null }));
    const client = { rpc } as unknown as Client;
    expect(await reviewSpec(client, 's1', 'approved', '  ')).toBe('approved');
    expect(rpc).toHaveBeenLastCalledWith('review_spec', { spec: 's1', verdict: 'approved' });
    await reviewSpec(client, 's1', 'changes_requested', ' Say how long it waits ');
    expect(rpc).toHaveBeenLastCalledWith('review_spec', {
      spec: 's1',
      verdict: 'changes_requested',
      note: 'Say how long it waits',
    });
  });

  it('gives Postgres’s refusal in its words', async () => {
    const rpc = async () => ({
      data: null,
      error: {
        code: '23514',
        message: 'Only a spec in review can be reviewed',
        details: '',
        hint: '',
      },
    });
    await expect(reviewSpec({ rpc } as unknown as Client, 's1', 'approved', '')).rejects.toThrow(
      'Only a spec in review can be reviewed.',
    );
  });
});
