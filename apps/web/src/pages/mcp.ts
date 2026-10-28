import { PUBLIC_SUPABASE_PUBLISHABLE_KEY, PUBLIC_SUPABASE_URL } from 'astro:env/client';
import type { APIRoute } from 'astro';
import { serveMcp } from '../lib/mcp/serve';

// Sulba's MCP server for coding agents (decision record 51), which answers on the Worker.
export const prerender = false;

export const ALL: APIRoute = ({ request }) =>
  serveMcp(request, {
    supabaseUrl: PUBLIC_SUPABASE_URL,
    publishableKey: PUBLIC_SUPABASE_PUBLISHABLE_KEY,
  });
