import { PUBLIC_SUPABASE_PUBLISHABLE_KEY, PUBLIC_SUPABASE_URL } from 'astro:env/client';
import type { APIRoute } from 'astro';
import { metadataOf } from '../../../lib/mcp/serve';

// Where an agent signs in to use Sulba's MCP server (RFC 9728), for the origin it's served at.
export const prerender = false;

export const GET: APIRoute = ({ url }) =>
  metadataOf(url.origin, {
    supabaseUrl: PUBLIC_SUPABASE_URL,
    publishableKey: PUBLIC_SUPABASE_PUBLISHABLE_KEY,
  });
