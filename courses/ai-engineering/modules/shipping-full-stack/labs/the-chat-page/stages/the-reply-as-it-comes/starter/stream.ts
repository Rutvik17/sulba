// The desk's reply as it comes: the events of a server-sent event stream, read from the bytes of a
// fetch's body as the HTML Standard parses them, then the reply's own events.
import type { Desk } from './api.ts';

/** An event of an event stream: its type, "message" unless it names another, and its data. */
export interface StreamEvent {
  readonly type: string;
  readonly data: string;
}

/** Each event of an event stream, as its bytes arrive, until the stream ends. */
export async function* events(body: ReadableStream<Uint8Array>): AsyncGenerator<StreamEvent> {
  throw new Error('events() is not written yet.');
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
  throw new Error('reply() is not written yet.');
}
