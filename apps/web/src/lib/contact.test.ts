import { expect, test, vi } from 'vitest';
import { checkFields, limits, type Message, readMessage, type Settings, send } from './contact';

const message: Message = {
  name: 'Ada Lovelace',
  email: 'ada@example.com',
  message: 'Hello',
  token: 'XXXX.DUMMY.TOKEN.XXXX',
};

const settings: Settings = {
  resendKey: 're_test',
  to: 'studio@example.com',
  from: 'Sulba <no-reply@example.com>',
  turnstileSecret: '1x0000000000000000000000000000000AA',
};

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

// A stand-in for the network: Turnstile's answer to the check, Resend's to the message.
function network(turnstile: Response | Error, resend: Response | Error = json({ id: 'email' })) {
  return vi.fn<typeof fetch>(async (input) => {
    const answer = String(input).includes('siteverify') ? turnstile : resend;
    if (answer instanceof Error) throw answer;
    return answer;
  });
}

test('each field says what it needs, and spaces alone count as empty', () => {
  const ok = { name: 'Ada Lovelace', email: 'ada@example.com', message: 'Hello' };

  expect(checkFields(ok)).toEqual({});
  expect(checkFields({ name: '', email: '', message: '' })).toEqual({
    name: 'missing',
    email: 'missing',
    message: 'missing',
  });
  expect(checkFields({ ...ok, name: '   ', message: '\n\t' })).toEqual({
    name: 'missing',
    message: 'missing',
  });
  expect(checkFields({ ...ok, email: 'ada@' })).toEqual({ email: 'format' });
  expect(checkFields({ ...ok, name: 'x'.repeat(limits.name + 1) })).toEqual({ name: 'long' });
});

test('a message needs every field, each within its limit, and an email address', () => {
  expect(readMessage({ ...message, name: '  Ada Lovelace  ' })).toEqual(message);
  expect(readMessage({ ...message, name: '   ' })).toBeUndefined();
  expect(readMessage({ ...message, email: 'ada' })).toBeUndefined();
  expect(readMessage({ ...message, message: 'x'.repeat(limits.message + 1) })).toBeUndefined();
  expect(readMessage({ ...message, token: undefined })).toBeUndefined();
  expect(readMessage('Hello')).toBeUndefined();
});

test('nothing is sent until all four settings are there', async () => {
  const fetch = network(json({ success: true }));

  const outcome = await send(
    message,
    { ...settings, resendKey: undefined },
    { fetch, ip: undefined },
  );

  expect(outcome).toEqual({ sent: false, problem: 'unavailable' });
  expect(fetch).not.toHaveBeenCalled();
});

test('a message that fails the Turnstile check is not sent', async () => {
  const fetch = network(json({ success: false, 'error-codes': ['invalid-input-response'] }));

  const outcome = await send(message, settings, { fetch, ip: '203.0.113.7' });

  expect(outcome).toEqual({ sent: false, problem: 'check' });
  expect(fetch).toHaveBeenCalledTimes(1);
});

test('a checked message goes to the studio, with the writer as the reply-to', async () => {
  const fetch = network(json({ success: true }));

  expect(await send(message, settings, { fetch, ip: '203.0.113.7' })).toEqual({ sent: true });

  const [check, sent] = fetch.mock.calls;
  const verify = check?.[1]?.body as URLSearchParams;
  expect(verify.get('secret')).toBe(settings.turnstileSecret);
  expect(verify.get('response')).toBe(message.token);
  expect(verify.get('remoteip')).toBe('203.0.113.7');
  expect(String(sent?.[0])).toBe('https://api.resend.com/emails');
  expect(new Headers(sent?.[1]?.headers).get('Authorization')).toBe('Bearer re_test');
  expect(JSON.parse(String(sent?.[1]?.body))).toEqual({
    from: settings.from,
    to: [settings.to],
    reply_to: message.email,
    subject: 'Message from Ada Lovelace',
    text: 'Hello\n\nAda Lovelace <ada@example.com>',
  });
});

test("a name can't add lines to the subject", async () => {
  const fetch = network(json({ success: true }));

  await send({ ...message, name: 'Ada\r\nBcc: someone@example.com' }, settings, {
    fetch,
    ip: undefined,
  });

  const body = JSON.parse(String(fetch.mock.calls[1]?.[1]?.body)) as { subject: string };
  expect(body.subject).toBe('Message from Ada Bcc: someone@example.com');
});

test('a network failure, or Resend refusing the message, is reported as not sent', async () => {
  const offline = network(new Error('offline'));
  const refused = network(json({ success: true }), json({ message: 'Invalid from' }, 422));

  expect(await send(message, settings, { fetch: offline, ip: undefined })).toEqual({
    sent: false,
    problem: 'failed',
  });
  expect(await send(message, settings, { fetch: refused, ip: undefined })).toEqual({
    sent: false,
    problem: 'failed',
  });
});
