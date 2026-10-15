import { describe, expect, it } from 'vitest';
import { isRating, type Review, ReviewLog, reviewOf } from './reviews.ts';

function memory(): Pick<Storage, 'getItem' | 'setItem'> & { map: Map<string, string> } {
  const map = new Map<string, string>();
  return {
    map,
    getItem: (key) => map.get(key) ?? null,
    setItem: (key, value) => void map.set(key, value),
  };
}

const at = new Date('2026-10-15T09:00:00Z');
const review = (id: string, rating: Review['rating'] = 3): Review =>
  reviewOf('crd_aaaaaa', rating, at, id);

describe('reviewOf', () => {
  it('records a card, its rating and when, under an id of its own', () => {
    expect(reviewOf('crd_aaaaaa', 4, at, 'id-1')).toEqual({
      id: 'id-1',
      card_id: 'crd_aaaaaa',
      rating: 4,
      reviewed_at: '2026-10-15T09:00:00.000Z',
    });
    expect(reviewOf('crd_aaaaaa', 3, at).id).toMatch(/^[0-9a-f-]{36}$/);
  });

  it('takes the four ratings and nothing else', () => {
    expect([0, 1, 2, 3, 4, 5, '3'].map(isRating)).toEqual([
      false,
      true,
      true,
      true,
      true,
      false,
      false,
    ]);
  });
});

describe('ReviewLog', () => {
  it('keeps reviews in storage, in the order they came', () => {
    const storage = memory();
    const log = new ReviewLog(storage);
    expect(log.all()).toEqual([]);
    log.add(review('id-1'));
    log.add(review('id-2', 1));
    expect(new ReviewLog(storage).all()).toEqual([review('id-1'), review('id-2', 1)]);
  });

  it('takes in only the reviews it lacks', () => {
    const log = new ReviewLog(memory());
    log.add(review('id-1'));
    log.takeIn([review('id-1'), review('id-2'), { ...review('id-3'), rating: 7 as 1 }]);
    expect(log.all().map((each) => each.id)).toEqual(['id-1', 'id-2']);
  });

  it("doesn't undo what another tab added", () => {
    const storage = memory();
    const first = new ReviewLog(storage);
    const second = new ReviewLog(storage);
    first.add(review('id-1'));
    second.add(review('id-2'));
    expect(new ReviewLog(storage).all().map((each) => each.id)).toEqual(['id-1', 'id-2']);
  });

  it('goes on counting reviews for the page when storage refuses them', () => {
    const log = new ReviewLog({
      getItem: () => null,
      setItem: () => {
        throw new Error('QuotaExceededError');
      },
    });
    log.add(review('id-1'));
    log.add(review('id-2'));
    expect(log.all().map((each) => each.id)).toEqual(['id-1', 'id-2']);
  });

  it('ignores what it can’t read', () => {
    const storage = memory();
    storage.map.set('sulba:reviews', 'not JSON');
    expect(new ReviewLog(storage).all()).toEqual([]);
    storage.map.set(
      'sulba:reviews',
      JSON.stringify([review('id-1'), { ...review('id-2'), card_id: 'stg_aaaaaa' }, null]),
    );
    expect(new ReviewLog(storage).all()).toEqual([review('id-1')]);
  });
});
