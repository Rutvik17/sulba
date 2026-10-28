import { PUBLIC_SUPABASE_URL } from 'astro:env/client';
import { SUPABASE_SECRET_KEY } from 'astro:env/server';
import type { APIRoute } from 'astro';
import { githubKeys, receive } from '../../lib/results';

// A report is recorded when it arrives, so this route runs on the Worker (decision record 1).
export const prerender = false;

export const POST: APIRoute = ({ request }) =>
  receive(
    request,
    { secretKey: SUPABASE_SECRET_KEY, supabaseUrl: PUBLIC_SUPABASE_URL, keys: githubKeys },
    { fetch },
  );

export const ALL: APIRoute = () => new Response(null, { status: 405, headers: { Allow: 'POST' } });
