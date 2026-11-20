import { PUBLIC_SUPABASE_PUBLISHABLE_KEY, PUBLIC_SUPABASE_URL } from 'astro:env/client';
import { ANTHROPIC_API_KEY, SUPABASE_SECRET_KEY } from 'astro:env/server';
import type { APIRoute } from 'astro';
import { check } from '../../../lib/agents/runs';

// Checks a running run for a member while the app shows it (decision record 64), on the Worker.
export const prerender = false;

export const POST: APIRoute = ({ request }) =>
  check(request, {
    supabaseUrl: PUBLIC_SUPABASE_URL,
    publishableKey: PUBLIC_SUPABASE_PUBLISHABLE_KEY,
    secretKey: SUPABASE_SECRET_KEY,
    anthropicKey: ANTHROPIC_API_KEY,
  });

export const ALL: APIRoute = () => new Response(null, { status: 405, headers: { Allow: 'POST' } });
