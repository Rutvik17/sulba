// Sends the outbox to Supabase and reads progress back (decision record 18).
import type { Client } from './client.ts';
import type { Attempt, Outbox } from './outbox.ts';

/** A stage passed in the learner's account, with its review if it's a Catch stage. */
export interface Passed {
  readonly stageId: string;
  readonly caught: readonly string[] | null;
  readonly problems: number | null;
}

/** How many attempts go in one request. */
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

type Outcome = 'sent' | 'refused' | 'retry';

async function insert(client: Client, attempts: readonly Attempt[]): Promise<Outcome> {
  const { error } = await client
    .from('attempts')
    .upsert([...attempts], { onConflict: 'id', ignoreDuplicates: true });
  if (!error) return 'sent';
  // Postgres's classes 22 and 23 are invalid data and broken constraints: that request can never
  // succeed. Anything else, a lost connection or the daily limit among them, may pass later.
  return /^2[23]/.test(error.code) ? 'refused' : 'retry';
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
