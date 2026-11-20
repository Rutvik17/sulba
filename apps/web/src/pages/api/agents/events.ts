import { PUBLIC_SUPABASE_PUBLISHABLE_KEY, PUBLIC_SUPABASE_URL } from 'astro:env/client';
import {
  ANTHROPIC_API_KEY,
  ANTHROPIC_WEBHOOK_SIGNING_KEY,
  SUPABASE_SECRET_KEY,
} from 'astro:env/server';
import type { APIRoute } from 'astro';
import { receive } from '../../../lib/agents/runs';

// Takes Anthropic's notices about the sessions of Sulba's agents (decision record 64), on the
// Worker.
export const prerender = false;

export const POST: APIRoute = ({ request }) =>
  receive(request, {
    supabaseUrl: PUBLIC_SUPABASE_URL,
    publishableKey: PUBLIC_SUPABASE_PUBLISHABLE_KEY,
    secretKey: SUPABASE_SECRET_KEY,
    anthropicKey: ANTHROPIC_API_KEY,
    webhookKey: ANTHROPIC_WEBHOOK_SIGNING_KEY,
  });

export const ALL: APIRoute = () => new Response(null, { status: 405, headers: { Allow: 'POST' } });
