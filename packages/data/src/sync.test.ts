import { describe, expect, it } from 'vitest';
import type { Client } from './client.ts';
import { type Attempt, attemptOf, Outbox } from './outbox.ts';
import { type Review, reviewOf } from './reviews.ts';
import { readReviews, send, sendReviews } from './sync.ts';

const stage = { id: 'stg_aaaaaa', version: '0123456789abcdef' };

function memory(): Pick<Storage, 'getItem' | 'setItem' | 'removeItem'> {
  const map = new Map<string, string>();
  return {
    getItem: (key) => map.get(key) ?? null,
    setItem: (key, value) => void map.set(key, value),
    removeItem: (key) => void map.delete(key),
  };
}

/** A client whose inserts answer as `answer` says, recording each request's rows. */
function client<Row = Attempt>(answer: (rows: Row[]) => { code: string } | null) {
  const requests: Row[][] = [];
  const fake = {
    from: () => ({
      upsert: async (rows: Row[]) => {
        requests.push(rows);
        const error = answer(rows);
        return { error: error && { ...error, message: '', details: '', hint: '' } };
      },
    }),
  };
  return { client: fake as unknown as Client, requests };
}

function filled(count: number): Outbox {
  const outbox = new Outbox(memory());
  for (let n = 0; n < count; n++) {
    outbox.add(attemptOf(stage, { kind: 'hint', hint: 1 }, 1, new Date(), `id-${n}`));
  }
  return outbox;
}

describe('send', () => {
  it('sends the outbox in batches of 100 and empties it', async () => {
    const outbox = filled(250);
    const { client: fake, requests } = client(() => null);
    expect(await send(fake, outbox)).toBe(true);
    expect(requests.map((attempts) => attempts.length)).toEqual([100, 100, 50]);
    expect(outbox.all()).toEqual([]);
  });

  it('keeps everything when a batch may pass later', async () => {
    const outbox = filled(3);
    const { client: fake } = client(() => ({ code: 'P0001' }));
    expect(await send(fake, outbox)).toBe(false);
    expect(outbox.all()).toHaveLength(3);
  });

  it('drops only the attempts the database refuses as invalid', async () => {
    const outbox = filled(3);
    const { client: fake } = client((attempts) =>
      attempts.some((attempt) => attempt.id === 'id-1') ? { code: '23514' } : null,
    );
    expect(await send(fake, outbox)).toBe(true);
    expect(outbox.all()).toEqual([]);
  });

  it('keeps an attempt that fails for another reason when sent alone', async () => {
    const outbox = filled(3);
    const { client: fake } = client((attempts) => {
      if (attempts.length > 1) return { code: '23514' };
      return attempts[0]?.id === 'id-2' ? { code: 'PGRST301' } : null;
    });
    expect(await send(fake, outbox)).toBe(false);
    expect(outbox.all().map((attempt) => attempt.id)).toEqual(['id-2']);
  });
});

const reviews = (count: number): Review[] =>
  Array.from({ length: count }, (_, n) => reviewOf('crd_aaaaaa', 3, new Date(), `id-${n}`));

describe('sendReviews', () => {
  it('sends reviews in batches of 100', async () => {
    const { client: fake, requests } = client<Review>(() => null);
    const sent = await sendReviews(fake, reviews(150));
    expect(requests.map((rows) => rows.length)).toEqual([100, 50]);
    expect(sent.size).toBe(150);
  });

  it('stops at a batch that may pass later', async () => {
    const { client: fake, requests } = client<Review>((rows) =>
      rows.some((review) => review.id === 'id-120') ? { code: 'P0001' } : null,
    );
    const sent = await sendReviews(fake, reviews(250));
    expect(requests).toHaveLength(2);
    expect(sent.size).toBe(100);
  });

  it('settles the reviews the database refuses as invalid, one at a time', async () => {
    const { client: fake } = client<Review>((rows) =>
      rows.some((review) => review.id === 'id-1') ? { code: '22007' } : null,
    );
    expect([...(await sendReviews(fake, reviews(3)))]).toEqual(['id-0', 'id-1', 'id-2']);
  });

  it('keeps back a review that fails for another reason when sent alone', async () => {
    const { client: fake } = client<Review>((rows) => {
      if (rows.length > 1) return { code: '23514' };
      return rows[0]?.id === 'id-1' ? { code: 'PGRST301' } : null;
    });
    expect([...(await sendReviews(fake, reviews(3)))]).toEqual(['id-0']);
  });
});

describe('readReviews', () => {
  it("reads the account's reviews a page at a time, and leaves out any it can't use", async () => {
    const rows = [
      ...reviews(1500).map((review) => ({ ...review, rating: review.rating as number })),
      { ...reviewOf('crd_aaaaaa', 3, new Date(), 'id-bad'), rating: 9 },
    ];
    const ranges: [number, number][] = [];
    const ordered = {
      range: async (from: number, to: number) => {
        ranges.push([from, to]);
        return { data: rows.slice(from, Math.min(to + 1, from + 1000)), error: null };
      },
    };
    const fake = {
      from: () => ({ select: () => ({ order: () => ({ order: () => ordered }) }) }),
    } as unknown as Client;
    const read = await readReviews(fake);
    expect(read).toHaveLength(1500);
    expect(read[0]).toEqual(rows[0]);
    expect(ranges).toEqual([
      [0, 999],
      [1000, 1999],
    ]);
  });
});
