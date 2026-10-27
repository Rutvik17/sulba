// The app's connection to Supabase, in a module of its own, so a page loads supabase-js only once
// the browser holds a session, as the site's pages do.
import { type Client, connect } from '@sulba/data/client';
import { projectUrl, publishableKey } from '@sulba/data/project';

let client: Client | undefined;

/** The app's one connection to Supabase, made the first time it's asked for. */
export function supabase(): Client {
  client ??= connect(
    import.meta.env.PUBLIC_SUPABASE_URL ?? projectUrl,
    import.meta.env.PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? publishableKey,
  );
  return client;
}
