import { describe, expect, it } from 'vitest';
import type { Client } from './client.ts';
import { type Attempt, attemptOf, Outbox } from './outbox.ts';
import { send } from './sync.ts';

const stage = { id: 'stg_aaaaaa', version: '0123456789abcdef' };

function memory(): Pick<Storage, 'getItem' | 'setItem' | 'removeItem'> {
  const map = new Map<string, string>();
  return {
    getItem: (key) => map.get(key) ?? null,
    setItem: (key, value) => void map.set(key, value),
    removeItem: (key) => void map.delete(key),
  };
}

/** A client whose inserts answer as `answer` says, recording each request's attempts. */
function client(answer: (attempts: Attempt[]) => { code: string } | null) {
  const requests: Attempt[][] = [];
  const fake = {
    from: () => ({
      upsert: async (attempts: Attempt[]) => {
        requests.push(attempts);
        const error = answer(attempts);
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
