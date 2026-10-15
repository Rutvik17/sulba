import { type Rating, type Review, reviewOf } from '@sulba/data/reviews';
import { describe, expect, it } from 'vitest';
import { dueAt, dueNow, intervals, nextDue, reviewLine, schedule, whenDue } from './review';

/** A moment in October 2026 where the learner is. */
const at = (day: number, hours: number, minutes = 0) => new Date(2026, 9, day, hours, minutes);
const card = (id: string) => ({ id });
let made = 0;
const review = (cardId: string, rating: Rating, when: Date): Review =>
  reviewOf(cardId, rating, when, `id-${String(made++).padStart(4, '0')}`);

/** A card first answered Good at 09:00 on the 15th, then Good again after its 10-minute step. */
const learned = () => [review('crd_aaaaaa', 3, at(15, 9)), review('crd_aaaaaa', 3, at(15, 9, 10))];

describe('schedule', () => {
  it('leaves a card never reviewed new', () => {
    expect(schedule([card('crd_aaaaaa')], [])).toEqual([
      { card: card('crd_aaaaaa'), reviews: [], memory: null },
    ]);
  });

  it("replays a card's reviews in the order they were given, however they arrived", () => {
    const log = [...learned(), review('crd_bbbbbb', 1, at(15, 9, 5))];
    const [first] = schedule([card('crd_aaaaaa')], log);
    const [second] = schedule([card('crd_aaaaaa')], [...log].reverse());
    expect(first?.reviews).toHaveLength(2);
    expect(second?.memory).toEqual(first?.memory);
    expect(first?.memory?.scheduled_days).toBe(2);
  });
});

describe('intervals', () => {
  it('gives a new card its learning steps, or a few days when it was easy', () => {
    expect(intervals(null, at(15, 9))).toEqual({
      1: '1 minute',
      2: '6 minutes',
      3: '10 minutes',
      4: '8 days',
    });
  });

  it('spaces a card that was remembered further, and brings back one that was forgotten', () => {
    const [scheduled] = schedule([card('crd_aaaaaa')], learned());
    const memory = scheduled?.memory ?? null;
    expect(intervals(memory, memory?.due ?? at(17, 9, 10))).toEqual({
      1: '10 minutes',
      2: '8 days',
      3: '11 days',
      4: '19 days',
    });
  });

  it('counts in months and years once intervals pass a month', () => {
    let when = at(15, 9);
    const log: Review[] = [];
    for (let n = 0; n < 2; n++) {
      log.push(review('crd_aaaaaa', 4, when));
      when = schedule([card('crd_aaaaaa')], log)[0]?.memory?.due ?? when;
    }
    const memory = schedule([card('crd_aaaaaa')], log)[0]?.memory ?? null;
    expect(intervals(memory, when)).toEqual({
      1: '10 minutes',
      2: '5.7 months',
      3: '8 months',
      4: '1.1 years',
    });
  });
});

describe('dueNow', () => {
  it('puts cards reviewed before first, in the order they fell due, then new cards', () => {
    const log = [
      review('crd_aaaaaa', 1, at(15, 9)),
      review('crd_bbbbbb', 1, at(15, 8)),
      review('crd_dddddd', 4, at(15, 9)),
    ];
    const scheduled = schedule(
      ['crd_aaaaaa', 'crd_bbbbbb', 'crd_cccccc', 'crd_dddddd'].map(card),
      log,
    );
    expect(dueNow(scheduled, at(15, 10)).map((each) => each.card.id)).toEqual([
      'crd_bbbbbb',
      'crd_aaaaaa',
      'crd_cccccc',
    ]);
  });

  it('makes a card due from the start of its day, once its interval is a day or more', () => {
    const scheduled = schedule([card('crd_aaaaaa')], learned());
    const memory = scheduled[0]?.memory;
    if (!memory) throw new Error('The card has no memory.');
    expect(dueAt(memory)).toEqual(at(17, 0));
    expect(dueNow(scheduled, at(16, 23, 59))).toEqual([]);
    expect(dueNow(scheduled, at(17, 0))).toHaveLength(1);
  });

  it('brings a card in a learning step early only when nothing else is due', () => {
    const log = [review('crd_aaaaaa', 3, at(15, 9))];
    const alone = schedule([card('crd_aaaaaa')], log);
    expect(dueNow(alone, at(15, 9, 1)).map((each) => each.card.id)).toEqual(['crd_aaaaaa']);
    const withNew = schedule([card('crd_aaaaaa'), card('crd_bbbbbb')], log);
    expect(dueNow(withNew, at(15, 9, 1)).map((each) => each.card.id)).toEqual(['crd_bbbbbb']);
  });

  it('brings a card in a learning step no more than 20 minutes early, and no other card early', () => {
    const [stepped] = schedule([card('crd_aaaaaa')], [review('crd_aaaaaa', 3, at(15, 9))]);
    if (!stepped?.memory) throw new Error('The card has no memory.');
    const later = [{ ...stepped, memory: { ...stepped.memory, due: at(15, 9, 30) } }];
    expect(dueNow(later, at(15, 9, 9))).toEqual([]);
    expect(dueNow(later, at(15, 9, 10))).toHaveLength(1);
    expect(dueNow(schedule([card('crd_aaaaaa')], learned()), at(16, 23, 50))).toEqual([]);
  });
});

describe('when cards are due', () => {
  it('finds the next card due, if any card has been reviewed', () => {
    expect(nextDue(schedule([card('crd_aaaaaa')], []))).toBeNull();
    expect(nextDue(schedule([card('crd_aaaaaa')], learned()))).toEqual(at(17, 0));
  });

  it('says when, from now', () => {
    expect(whenDue(at(15, 9, 9), at(15, 9))).toBe('in 9 minutes');
    expect(whenDue(at(15, 9, 0), at(15, 9))).toBe('in 1 minute');
    expect(whenDue(at(15, 14, 30), at(15, 9))).toBe('today at 14:30');
    expect(whenDue(at(17, 0), at(15, 9))).toBe('on Saturday 17 October 2026');
  });

  it('lists a review with its date, time and rating', () => {
    expect(reviewLine(review('crd_aaaaaa', 3, at(15, 9, 10)))).toBe(
      'Thursday 15 October 2026, 09:10: Good',
    );
  });
});
