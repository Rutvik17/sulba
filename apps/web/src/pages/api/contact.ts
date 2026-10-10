import { CONTACT_FROM, CONTACT_TO, RESEND_API_KEY, TURNSTILE_SECRET_KEY } from 'astro:env/server';
import type { APIRoute } from 'astro';
import { type Problem, readMessage, send } from '../../lib/contact';

// A message is sent when it arrives, so this route runs on the Worker (decision record 1).
export const prerender = false;

const status: Record<Problem, number> = { invalid: 400, check: 403, unavailable: 503, failed: 502 };
// Room for the longest message in any script, well under what the Worker accepts.
const MAX_BYTES = 32_768;

const reply = (body: object, code: number) =>
  new Response(JSON.stringify(body), {
    status: code,
    headers: { 'Content-Type': 'application/json' },
  });

export const POST: APIRoute = async ({ request, clientAddress }) => {
  const text = await request.text();
  let body: unknown;
  try {
    body = text.length <= MAX_BYTES ? JSON.parse(text) : undefined;
  } catch {
    body = undefined;
  }
  const message = readMessage(body);
  if (!message) return reply({ problem: 'invalid' }, status.invalid);

  const outcome = await send(
    message,
    {
      resendKey: RESEND_API_KEY,
      to: CONTACT_TO,
      from: CONTACT_FROM,
      turnstileSecret: TURNSTILE_SECRET_KEY,
    },
    { fetch, ip: clientAddress },
  );
  return outcome.sent
    ? reply({ sent: true }, 200)
    : reply({ problem: outcome.problem }, status[outcome.problem]);
};

export const ALL: APIRoute = () => new Response(null, { status: 405, headers: { Allow: 'POST' } });
