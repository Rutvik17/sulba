// Spaced review (decision record 20). A card's schedule comes from its reviews alone, replayed in
// the order they were given through FSRS-6, so every device that holds the same reviews works out
// the same schedule.
import { localDay } from '@sulba/data/outbox';
import type { Rating, Review } from '@sulba/data/reviews';
import { createEmptyCard, fsrs, type Grade, Rating as Grades, type Card as Memory } from 'ts-fsrs';
import { dateOf } from './study';

export type { Memory };

const scheduler = fsrs({
  request_retention: 0.9,
  maximum_interval: 36_500,
  enable_fuzz: false,
  enable_short_term: true,
  learning_steps: ['1m', '10m'],
  relearning_steps: ['10m'],
});

const grades: Readonly<Record<Rating, Grade>> = {
  1: Grades.Again,
  2: Grades.Hard,
  3: Grades.Good,
  4: Grades.Easy,
};

/** The ratings, in the order their buttons show. */
export const ratings: readonly { readonly rating: Rating; readonly name: string }[] = [
  { rating: 1, name: 'Again' },
  { rating: 2, name: 'Hard' },
  { rating: 3, name: 'Good' },
  { rating: 4, name: 'Easy' },
];

/** How early a card in a learning step comes when nothing else is due, as Anki's default has it. */
const learnAhead = 20 * 60_000;

/** A card, its reviews oldest first, and the memory they leave, or null for a card never reviewed. */
export interface Scheduled<C> {
  readonly card: C;
  readonly reviews: readonly Review[];
  readonly memory: Memory | null;
}

/** Each card with its reviews from the log and the memory they leave, in the order cards come. */
export function schedule<C extends { readonly id: string }>(
  cards: readonly C[],
  log: readonly Review[],
): Scheduled<C>[] {
  const byCard = new Map<string, Review[]>();
  for (const review of log) {
    const reviews = byCard.get(review.card_id);
    if (reviews) reviews.push(review);
    else byCard.set(review.card_id, [review]);
  }
  return cards.map((card) => {
    const reviews = (byCard.get(card.id) ?? []).sort(inOrder);
    return { card, reviews, memory: memoryOf(reviews) };
  });
}

function inOrder(a: Review, b: Review): number {
  const time = Date.parse(a.reviewed_at) - Date.parse(b.reviewed_at);
  if (time !== 0) return time;
  return a.id < b.id ? -1 : 1;
}

function memoryOf(reviews: readonly Review[]): Memory | null {
  let memory: Memory | null = null;
  for (const review of reviews) {
    const at = new Date(review.reviewed_at);
    memory = scheduler.next(memory ?? createEmptyCard(at), at, grades[review.rating]).card;
  }
  return memory;
}

/**
 * When a reviewed card falls due: in a learning step, at its time; with an interval of a day or
 * more, from the start of its day where the learner is.
 */
export function dueAt(memory: Memory): Date {
  if (memory.scheduled_days < 1) return memory.due;
  const day = new Date(memory.due);
  day.setHours(0, 0, 0, 0);
  return day;
}

/**
 * The cards to review now: those reviewed before, in the order they fell due, then new cards in
 * the order they come. When none is due, a card in a learning step that falls due within 20
 * minutes comes early.
 */
export function dueNow<C>(scheduled: readonly Scheduled<C>[], now: Date): Scheduled<C>[] {
  const due = scheduled.filter(({ memory }) => memory && dueAt(memory) <= now).sort(byDue);
  const fresh = scheduled.filter(({ memory }) => !memory);
  if (due.length > 0 || fresh.length > 0) return [...due, ...fresh];
  return scheduled
    .filter(
      ({ memory }) =>
        memory && memory.scheduled_days < 1 && memory.due.getTime() - now.getTime() <= learnAhead,
    )
    .sort(byDue);
}

function byDue<C>(a: Scheduled<C>, b: Scheduled<C>): number {
  return (a.memory?.due.getTime() ?? 0) - (b.memory?.due.getTime() ?? 0);
}

/** When the next card falls due, if any card has been reviewed. */
export function nextDue<C>(scheduled: readonly Scheduled<C>[]): Date | null {
  const times = scheduled.flatMap(({ memory }) => (memory ? [dueAt(memory).getTime()] : []));
  return times.length > 0 ? new Date(Math.min(...times)) : null;
}

/** When the card comes back after each rating, as its button shows it: "10 minutes", "3 days". */
export function intervals(memory: Memory | null, now: Date): Record<Rating, string> {
  const preview = scheduler.repeat(memory ?? createEmptyCard(now), now);
  const after = (rating: Rating) => intervalOf(preview[grades[rating]].card, now);
  return { 1: after(1), 2: after(2), 3: after(3), 4: after(4) };
}

function intervalOf(memory: Memory, now: Date): string {
  if (memory.scheduled_days >= 1) return daysOf(memory.scheduled_days);
  const minutes = Math.max(1, Math.round((memory.due.getTime() - now.getTime()) / 60_000));
  return minutes < 60 ? count(minutes, 'minute') : count(Math.round(minutes / 60), 'hour');
}

/** Days, then months and years to a tenth past a month: "3 days", "1.5 months", "2 years". */
function daysOf(days: number): string {
  if (days < 31) return count(days, 'day');
  if (days < 365) return count(Math.round(days / 3.044) / 10, 'month');
  return count(Math.round(days / 36.525) / 10, 'year');
}

function count(value: number, unit: string): string {
  return `${value} ${value === 1 ? unit : `${unit}s`}`;
}

/** When a card is due, from now: "in 9 minutes", "today at 14:30", "on Friday 16 October 2026". */
export function whenDue(due: Date, now: Date): string {
  const minutes = Math.ceil((due.getTime() - now.getTime()) / 60_000);
  if (minutes < 60) return `in ${count(Math.max(1, minutes), 'minute')}`;
  if (localDay(due) === localDay(now)) return `today at ${timeOf(due)}`;
  return `on ${dateOf(localDay(due))}`;
}

/** A review as the card's history lists it: "Thursday 15 October 2026, 09:10: Good". */
export function reviewLine(review: Review): string {
  const at = new Date(review.reviewed_at);
  const name = ratings.find(({ rating }) => rating === review.rating)?.name ?? '';
  return `${dateOf(localDay(at))}, ${timeOf(at)}: ${name}`;
}

function timeOf(at: Date): string {
  return `${String(at.getHours()).padStart(2, '0')}:${String(at.getMinutes()).padStart(2, '0')}`;
}
