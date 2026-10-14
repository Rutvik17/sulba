// Signing in with GitHub or Google, signing out, and closing an account (decision record 19).
import type { User } from '@supabase/supabase-js';
import type { Client } from './client.ts';

export const providers = { github: 'GitHub', google: 'Google' } as const;

export type Provider = keyof typeof providers;

/** The signed-in learner, as the account page shows them. */
export interface Learner {
  readonly email: string | null;
  /** The provider they signed in with, when it's one the site offers. */
  readonly provider: Provider | null;
}

export function learnerOf(user: User): Learner {
  const provider: unknown = user.app_metadata.provider;
  return {
    email: user.email ?? null,
    provider: provider === 'github' || provider === 'google' ? provider : null,
  };
}

/**
 * Sends the browser to the provider. It comes back to `returnTo`, with a code the client on that
 * page trades for a session.
 */
export async function signIn(client: Client, provider: Provider, returnTo: string): Promise<void> {
  const { error } = await client.auth.signInWithOAuth({
    provider,
    options: { redirectTo: returnTo },
  });
  if (error) throw error;
}

/** The learner signed in in this browser, or null. */
export async function currentLearner(client: Client): Promise<Learner | null> {
  const { data } = await client.auth.getSession();
  return data.session ? learnerOf(data.session.user) : null;
}

/** Signs out of this browser only; other devices stay signed in. */
export async function signOut(client: Client): Promise<void> {
  const { error } = await client.auth.signOut({ scope: 'local' });
  if (error) throw error;
}

/**
 * Deletes the account and everything it recorded, then signs this browser out. What this browser
 * keeps on its own, such as a lab's code, stays.
 */
export async function closeAccount(client: Client): Promise<void> {
  const { error } = await client.rpc('close_account');
  if (error) throw error;
  await client.auth.signOut({ scope: 'local' });
}
