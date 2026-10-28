// What the app tells a person when Postgres refuses what they asked, or the request fails.
import type { PostgrestError } from '@supabase/supabase-js';

/** A refusal or failure, in words to show the person who asked. */
export class Refusal extends Error {
  override name = 'Refusal';
}

/**
 * The words for a refusal. The functions in Postgres raise theirs for people to read, and each
 * becomes a sentence; anything else, such as a lost connection, gets a general one, and `taken`
 * names a duplicate.
 */
export function refusal(error: PostgrestError, taken?: string): Refusal {
  if (error.code === '23505' && taken) return new Refusal(taken);
  const said = ['42501', '23514', '54000', 'P0002'].includes(error.code);
  const technical = /constraint|permission denied|violates/.test(error.message);
  if (!said || technical) return new Refusal('Sulba couldn’t do that just now. Try again.');
  return new Refusal(/[.!?]$/.test(error.message) ? error.message : `${error.message}.`);
}
