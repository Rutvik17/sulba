import { env } from 'cloudflare:workers';
import type { APIRoute } from 'astro';

// The app draws its pages in the browser (decision record 47), so every address under /app/ but
// its files answers with its page. The Worker runs first for those addresses (run_worker_first in
// wrangler.jsonc), as a browser opening one would otherwise get the site's 404 page (decision
// record 54).
export const prerender = false;

export const GET: APIRoute = ({ request }) => env.ASSETS.fetch(new URL('/app/', request.url));
