import { expect, it } from 'vitest';
import type { Client } from './client.ts';
import { workOf } from './work.ts';

/** A query that answers with `result` whatever filters it's given, as PostgREST would. */
function answering(result: unknown) {
  const query: object = new Proxy(
    {},
    {
      get: (_, key) =>
        key === 'then' ? (resolve: (value: unknown) => void) => resolve(result) : () => query,
    },
  );
  return query;
}

const spec = (number: number, updatedAt: string) => ({
  id: `s${number}`,
  number,
  title: `Spec ${number}`,
  status: 'in_review',
  owner_id: 'ada',
  updated_at: updatedAt,
});

it('asks for the reviews waiting, and those whose spec changed after a request for changes', async () => {
  const tables: Record<string, unknown> = {
    spec_reviews: {
      data: [
        {
          verdict: 'pending',
          requested_by: 'ada',
          requested_at: '2026-10-27T09:00:00Z',
          answered_at: null,
          specs: spec(1, '2026-10-27T09:00:00Z'),
        },
        {
          verdict: 'changes_requested',
          requested_by: 'ada',
          requested_at: '2026-10-27T09:00:00Z',
          answered_at: '2026-10-27T10:00:00Z',
          specs: spec(2, '2026-10-27T11:00:00+00:00'),
        },
        {
          verdict: 'changes_requested',
          requested_by: 'ada',
          requested_at: '2026-10-27T09:00:00Z',
          answered_at: '2026-10-27T10:00:00Z',
          specs: spec(3, '2026-10-27T09:30:00Z'),
        },
      ],
      error: null,
    },
    specs: {
      data: [
        {
          id: 's4',
          number: 4,
          title: 'Spec 4',
          status: 'in_review',
          updated_at: '2026-10-27T09:00:00Z',
          spec_reviews: [{ verdict: 'approved' }, { verdict: 'pending' }],
        },
      ],
      error: null,
    },
    criterion_proofs: { data: [], error: null },
  };
  const client = { from: (table: string) => answering(tables[table]) } as unknown as Client;

  const work = await workOf(client, 'w1', 'ben');

  expect(work.asked.map((each) => [each.specNumber, each.changedSinceAnswer])).toEqual([
    [1, false],
    [2, true],
  ]);
  expect(work.owned).toEqual([
    {
      id: 's4',
      number: 4,
      title: 'Spec 4',
      status: 'in_review',
      updatedAt: '2026-10-27T09:00:00Z',
      verdicts: ['approved', 'pending'],
    },
  ]);
  expect(work.failing).toEqual([]);
});
