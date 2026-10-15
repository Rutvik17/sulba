// Sends the outbox to Supabase and reads progress back (decision record 18), and sends and reads
// reviews (decision record 20).
import type { Client } from './client.ts';
import type { Attempt, Outbox } from './outbox.ts';
import { isRating, type Review } from './reviews.ts';
import { readAll } from './rows.ts';

/** A stage passed in the learner's account, with its review if it's a Catch stage. */
export interface Passed {
  readonly stageId: string;
  readonly caught: readonly string[] | null;
  readonly problems: number | null;
}

/** How many attempts or reviews go in one request. */
const batch = 100;

/**
 * Sends the outbox, oldest first, until it's empty or a batch can't go. Returns whether it emptied.
 * An attempt the database refuses as invalid is dropped, since it can never be accepted; the rest
 * wait, through a lost connection or the daily limit, for the next try.
 */
export async function send(client: Client, outbox: Outbox): Promise<boolean> {
  for (;;) {
    const pending = outbox.all().slice(0, batch);
    if (pending.length === 0) return true;
    const sent = await insert(client, pending);
    if (sent === 'retry') return false;
    if (sent === 'refused') {
      const kept = await sendOneByOne(client, pending);
      outbox.remove(new Set(pending.filter((attempt) => !kept.has(attempt.id)).map(idOf)));
      if (kept.size > 0) return false;
    } else {
      outbox.remove(new Set(pending.map(idOf)));
    }
  }
}

/** Each stage passed in the learner's account. */
export async function readPassed(client: Client): Promise<Passed[]> {
  const { data, error } = await client
    .from('progress')
    .select('stage_id, caught, problems')
    .not('passed_at', 'is', null);
  if (error) throw error;
  return data.map((row) => ({ stageId: row.stage_id, caught: row.caught, problems: row.problems }));
}

/** Every review in the learner's account, in the order they arrived. */
export async function readReviews(client: Client): Promise<Review[]> {
  const rows = await readAll((from, to) =>
    client
      .from('reviews')
      .select('id, card_id, rating, reviewed_at')
      .order('created_at')
      .order('id')
      .range(from, to),
  );
  return rows.flatMap(({ rating, ...review }) => (isRating(rating) ? [{ ...review, rating }] : []));
}

/**
 * Sends reviews, oldest first, until they're all sent or a batch can't go. Returns the ids it
 * settled: those sent, and those the database refuses as invalid, which stay in this browser's log
 * but aren't worth sending again.
 */
export async function sendReviews(
  client: Client,
  reviews: readonly Review[],
): Promise<Set<string>> {
  const settled = new Set<string>();
  for (let from = 0; from < reviews.length; from += batch) {
    const pending = reviews.slice(from, from + batch);
    const outcome = await insertReviews(client, pending);
    if (outcome === 'retry') return settled;
    if (outcome === 'refused') {
      for (const review of pending) {
        if ((await insertReviews(client, [review])) === 'retry') return settled;
        settled.add(review.id);
      }
    } else {
      for (const review of pending) settled.add(review.id);
    }
  }
  return settled;
}

type Outcome = 'sent' | 'refused' | 'retry';

function outcomeOf({ error }: { readonly error: { readonly code: string } | null }): Outcome {
  if (!error) return 'sent';
  // Postgres's classes 22 and 23 are invalid data and broken constraints: that request can never
  // succeed. Anything else, a lost connection or the daily limit among them, may pass later.
  return /^2[23]/.test(error.code) ? 'refused' : 'retry';
}

async function insertReviews(client: Client, reviews: readonly Review[]): Promise<Outcome> {
  return outcomeOf(
    await client.from('reviews').upsert([...reviews], { onConflict: 'id', ignoreDuplicates: true }),
  );
}

async function insert(client: Client, attempts: readonly Attempt[]): Promise<Outcome> {
  return outcomeOf(
    await client
      .from('attempts')
      .upsert([...attempts], { onConflict: 'id', ignoreDuplicates: true }),
  );
}

/** Sends a refused batch one attempt at a time, and returns the ids still waiting. */
async function sendOneByOne(client: Client, attempts: readonly Attempt[]): Promise<Set<string>> {
  const waiting = new Set<string>();
  for (const attempt of attempts) {
    if ((await insert(client, [attempt])) === 'retry') waiting.add(attempt.id);
  }
  return waiting;
}

function idOf(attempt: Attempt): string {
  return attempt.id;
}
