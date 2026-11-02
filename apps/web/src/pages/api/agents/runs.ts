import { PUBLIC_SUPABASE_PUBLISHABLE_KEY, PUBLIC_SUPABASE_URL } from 'astro:env/client';
import { ANTHROPIC_API_KEY, SUPABASE_SECRET_KEY } from 'astro:env/server';
import type { APIRoute } from 'astro';
import { start } from '../../../lib/agents/runs';

// Starts a run of one of Sulba's agents for a member (decision record 64), on the Worker.
export const prerender = false;

export const POST: APIRoute = ({ request }) =>
  start(request, {
    supabaseUrl: PUBLIC_SUPABASE_URL,
    publishableKey: PUBLIC_SUPABASE_PUBLISHABLE_KEY,
    secretKey: SUPABASE_SECRET_KEY,
    anthropicKey: ANTHROPIC_API_KEY,
  });

export const ALL: APIRoute = () => new Response(null, { status: 405, headers: { Allow: 'POST' } });
