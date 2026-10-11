/*
  The contact form's server side. A message is checked, its Turnstile token is verified with
  Cloudflare, and it is sent to the studio's inbox through Resend, with the writer as the reply-to.
  The settings and fetch are passed in, so the steps can be tested without the network.
*/

export const limits = { name: 100, email: 254, message: 5000, token: 2048 } as const;

export interface Message {
  name: string;
  email: string;
  message: string;
  token: string;
}

/** The fields a writer fills in. */
export const fields = ['name', 'email', 'message'] as const;
export type Field = (typeof fields)[number];

/** What's wrong with a field: it's empty (spaces alone count), it's too long, or it isn't an email address. */
export type FieldProblem = 'missing' | 'long' | 'format';

export interface Settings {
  resendKey: string | undefined;
  to: string | undefined;
  from: string | undefined;
  turnstileSecret: string | undefined;
}

/** Why a message wasn't sent; the page words each one for the writer. */
export type Problem = 'invalid' | 'check' | 'unavailable' | 'failed';

export type Outcome = { sent: true } | { sent: false; problem: Problem };

const emailShape = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const TIMEOUT = 10_000;

/** Each field's problem, if it has one. The form and the server check a message the same way. */
export function checkFields(values: Record<Field, string>): Partial<Record<Field, FieldProblem>> {
  const found: Partial<Record<Field, FieldProblem>> = {};
  for (const field of fields) {
    const value = values[field].trim();
    if (!value) found[field] = 'missing';
    else if (value.length > limits[field]) found[field] = 'long';
    else if (field === 'email' && !emailShape.test(value)) found[field] = 'format';
  }
  return found;
}

/** The message in a request's JSON body, or undefined if a field is missing or out of bounds. */
export function readMessage(body: unknown): Message | undefined {
  if (typeof body !== 'object' || body === null) return undefined;
  const field = (key: keyof Message) => {
    const value = (body as Record<string, unknown>)[key];
    return typeof value === 'string' ? value.trim() : '';
  };
  const message = {
    name: field('name'),
    email: field('email'),
    message: field('message'),
    token: field('token'),
  };
  const tokenFits = message.token.length > 0 && message.token.length <= limits.token;
  return tokenFits && Object.keys(checkFields(message)).length === 0 ? message : undefined;
}

export async function send(
  message: Message,
  settings: Settings,
  { fetch, ip }: { fetch: typeof globalThis.fetch; ip: string | undefined },
): Promise<Outcome> {
  const { resendKey, to, from, turnstileSecret } = settings;
  if (!resendKey || !to || !from || !turnstileSecret)
    return { sent: false, problem: 'unavailable' };

  const check = new URLSearchParams({
    secret: turnstileSecret,
    response: message.token,
    idempotency_key: crypto.randomUUID(),
  });
  if (ip) check.set('remoteip', ip);
  try {
    const verdict = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method: 'POST',
      body: check,
      signal: AbortSignal.timeout(TIMEOUT),
    });
    const { success } = (await verdict.json()) as { success?: boolean };
    if (success !== true) return { sent: false, problem: 'check' };
  } catch {
    return { sent: false, problem: 'failed' };
  }

  // A name is one line of the subject, however it was typed.
  const name = message.name.replace(/\s+/g, ' ');
  try {
    const sent = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${resendKey}`,
        'Content-Type': 'application/json',
        'Idempotency-Key': crypto.randomUUID(),
      },
      body: JSON.stringify({
        from,
        to: [to],
        reply_to: message.email,
        subject: `Message from ${name}`,
        text: `${message.message}\n\n${name} <${message.email}>`,
      }),
      signal: AbortSignal.timeout(TIMEOUT),
    });
    return sent.ok ? { sent: true } : { sent: false, problem: 'failed' };
  } catch {
    return { sent: false, problem: 'failed' };
  }
}
