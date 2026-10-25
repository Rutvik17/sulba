// The desk's reply as it comes: the events of a server-sent event stream, read from the bytes of a
// fetch's body as the HTML Standard parses them, then the reply's own events.
import { ApiError, type Desk } from './api.ts';

/** An event of an event stream: its type, "message" unless it names another, and its data. */
export interface StreamEvent {
  readonly type: string;
  readonly data: string;
}

/** What an event's fields have given so far, until a blank line ends it. */
interface Pending {
  type: string;
  data: string;
}

/** Each event of an event stream, as its bytes arrive, until the stream ends. */
export async function* events(body: ReadableStream<Uint8Array>): AsyncGenerator<StreamEvent> {
  const reader = body.getReader();
  // A character's bytes can arrive in two chunks: the decoder keeps the first part of one until
  // the rest comes. It also drops a byte order mark at the start.
  const decoder = new TextDecoder();
  const pending: Pending = { type: '', data: '' };
  let text = '';
  try {
    for (;;) {
      const { done, value } = await reader.read();
      text += done ? decoder.decode() : decoder.decode(value, { stream: true });
      // A line ends at CRLF, LF or CR, but a CR at the end of what has come may be the first half
      // of a CRLF, so it waits for the next chunk, unless the stream has ended.
      const ends = done ? /\r\n|\r|\n/g : /\r\n|\r(?!$)|\n/g;
      let start = 0;
      for (const end of text.matchAll(ends)) {
        const event = line(text.slice(start, end.index), pending);
        start = end.index + end[0].length;
        if (event !== null) yield event;
      }
      text = text.slice(start);
      // An event the stream ends in the middle of is never dispatched.
      if (done) return;
    }
  } finally {
    // A reader that stops early, or fails, cancels the stream, so the connection is let go.
    await reader.cancel().catch(() => undefined);
  }
}

/** Takes one line of the stream into the pending event, and gives the event a blank line ends. */
function line(text: string, pending: Pending): StreamEvent | null {
  if (text === '') {
    const { type, data } = pending;
    pending.type = '';
    pending.data = '';
    if (data === '') return null;
    return { type: type || 'message', data: data.endsWith('\n') ? data.slice(0, -1) : data };
  }
  if (text.startsWith(':')) return null;
  const colon = text.indexOf(':');
  const field = colon === -1 ? text : text.slice(0, colon);
  const value = colon === -1 ? '' : text.slice(colon + 1).replace(/^ /, '');
  if (field === 'event') pending.type = value;
  else if (field === 'data') pending.data += `${value}\n`;
  return null;
}

/** An event of the desk's reply. */
export type ReplyEvent =
  | { readonly kind: 'text'; readonly delta: string }
  | { readonly kind: 'tool'; readonly name: string }
  | { readonly kind: 'done'; readonly content: string }
  | { readonly kind: 'error'; readonly title: string };

/**
 * The desk's reply to the caller's message, event by event, until it's done or fails. A reply
 * whose stream ends before either ends with an error of its own.
 */
export async function* reply(
  desk: Desk,
  id: string,
  content: string,
  signal?: AbortSignal,
): AsyncGenerator<ReplyEvent> {
  const response = await desk.say(id, content, signal);
  if (response.body === null)
    throw new ApiError(response.status, 'The reply had no body.', null, []);
  for await (const event of events(response.body)) {
    const data = JSON.parse(event.data) as Record<string, string>;
    if (event.type === 'text') yield { kind: 'text', delta: data.delta ?? '' };
    else if (event.type === 'tool') yield { kind: 'tool', name: data.name ?? '' };
    else if (event.type === 'done' || event.type === 'error') {
      yield event.type === 'done'
        ? { kind: 'done', content: data.content ?? '' }
        : { kind: 'error', title: data.title ?? '' };
      return;
    }
  }
  yield { kind: 'error', title: 'The reply stopped before its end.' };
}
