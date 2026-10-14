// The site's one connection to Supabase (decision record 4). It runs in the browser, with the
// publishable key, so row-level security decides everything it can reach.
import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import type { Database } from './database.ts';
import { sessionKey } from './session.ts';

export type Client = SupabaseClient<Database>;

/**
 * A client that signs in with PKCE (decision record 19), keeps the session in local storage under
 * the site's own key, and renews it before it expires. On a page that a provider sends the learner
 * back to, it trades the code in the address for a session as it starts.
 */
export function connect(url: string, publishableKey: string): Client {
  return createClient<Database>(url, publishableKey, {
    auth: { flowType: 'pkce', storageKey: sessionKey },
  });
}
