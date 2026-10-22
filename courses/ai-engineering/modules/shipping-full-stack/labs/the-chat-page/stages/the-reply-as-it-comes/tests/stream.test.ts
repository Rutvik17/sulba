import assert from 'node:assert/strict';
import { test } from 'node:test';
import { Desk } from '#api.ts';
import { events, reply, type StreamEvent } from '#stream.ts';

/** A stream of these chunks of bytes, each a string's UTF-8 or bytes as they are. */
function chunked(...chunks: (string | Uint8Array)[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    pull(controller) {
      const chunk = chunks.shift();
      if (chunk === undefined) controller.close();
      else controller.enqueue(typeof chunk === 'string' ? encoder.encode(chunk) : chunk);
    },
  });
}

async function all(body: ReadableStream<Uint8Array>): Promise<StreamEvent[]> {
  const found: StreamEvent[] = [];
  for await (const event of events(body)) found.push(event);
  return found;
}

test('tst_gdo0u5 An event is its type and its data, given when a blank line ends it', async () => {
  assert.deepEqual(await all(chunked('event: text\ndata: {"delta":"Hi"}\n\n')), [
    { type: 'text', data: '{"delta":"Hi"}' },
  ]);
});

test('tst_96rt05 Lines of data join with a line feed, and an event without a type is a message', async () => {
  assert.deepEqual(await all(chunked('data: YHOO\ndata: +2\ndata: 10\n\n')), [
    { type: 'message', data: 'YHOO\n+2\n10' },
  ]);
});

test('tst_s60azm A line ends at CRLF, LF or CR', async () => {
  assert.deepEqual(await all(chunked('data: a\r\n\r\ndata: b\n\ndata: c\r\r')), [
    { type: 'message', data: 'a' },
    { type: 'message', data: 'b' },
    { type: 'message', data: 'c' },
  ]);
});

test('tst_xy6xat A CRLF split between two chunks ends one line, not two', async () => {
  assert.deepEqual(await all(chunked('data: a\r', '\ndata: b\r', '\n\r', '\n')), [
    { type: 'message', data: 'a\nb' },
  ]);
});

test('tst_2n0txr A character whose bytes come in two chunks is read whole', async () => {
  const bytes = new TextEncoder().encode('data: café ☕\n\n');
  const cut = bytes.indexOf(0xc3) + 1;
  assert.deepEqual(
    await all(chunked(bytes.slice(0, cut), bytes.slice(cut, cut + 4), bytes.slice(cut + 4))),
    [{ type: 'message', data: 'café ☕' }],
  );
});

test('tst_cdtfd8 Comments, unknown fields and a byte order mark are left out', async () => {
  const stream = chunked(
    '﻿: keep-alive\nretry: 3000\nid: 7\nevent: tool\ndata:{"name":"search"}\n\n',
  );
  assert.deepEqual(await all(stream), [{ type: 'tool', data: '{"name":"search"}' }]);
});

test('tst_xh1sb5 A field without a colon has no value, and only one space after a colon goes', async () => {
  assert.deepEqual(await all(chunked('data\ndata:  two\n\n')), [
    { type: 'message', data: '\n two' },
  ]);
});

test('tst_248p0n An event with no data, or one the stream ends in the middle of, is not given', async () => {
  assert.deepEqual(await all(chunked('event: text\n\ndata: whole\n\ndata: half')), [
    { type: 'message', data: 'whole' },
  ]);
});

test('tst_df49ld A reader that stops early cancels the stream', async () => {
  let cancelled = false;
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    pull(controller) {
      controller.enqueue(encoder.encode('data: more\n\n'));
    },
    cancel() {
      cancelled = true;
    },
  });
  for await (const event of events(body)) {
    assert.equal(event.data, 'more');
    break;
  }
  assert.equal(cancelled, true);
});

/** A desk whose replies are these event streams, and the requests it was sent. */
function answering(...bodies: ReadableStream<Uint8Array>[]) {
  const signals: (AbortSignal | null)[] = [];
  const fetcher = async (_input: RequestInfo | URL, init?: RequestInit) => {
    signals.push(init?.signal ?? null);
    return new Response(bodies.shift() ?? null, {
      headers: { 'Content-Type': 'text/event-stream' },
    });
  };
  return { desk: new Desk(fetcher), signals };
}

test("tst_ssg8u4 The desk's reply gives its text, its tools and its end", async () => {
  const { desk } = answering(
    chunked(
      'event: tool\ndata: {"name":"search"}\n\n',
      'event: text\ndata: {"delta":"We open"}\n\nevent: text\ndata: {"delta":" at 9."}\n\n',
      'event: done\ndata: {"content":"We open at 9."}\n\nevent: text\ndata: {"delta":"!"}\n\n',
    ),
  );
  const seen = [];
  for await (const event of reply(desk, 'c1', 'When do you open?')) seen.push(event);
  assert.deepEqual(seen, [
    { kind: 'tool', name: 'search' },
    { kind: 'text', delta: 'We open' },
    { kind: 'text', delta: ' at 9.' },
    { kind: 'done', content: 'We open at 9.' },
  ]);
});

test('tst_ecr7n7 A reply that fails gives its error, and one cut short gives an error of its own', async () => {
  const { desk } = answering(
    chunked('event: error\ndata: {"title":"The reply took too long."}\n\n'),
    chunked('event: text\ndata: {"delta":"We"}\n\n'),
  );
  const failed = [];
  for await (const event of reply(desk, 'c1', 'Hello')) failed.push(event);
  assert.deepEqual(failed, [{ kind: 'error', title: 'The reply took too long.' }]);
  const cut = [];
  for await (const event of reply(desk, 'c1', 'Hello')) cut.push(event);
  assert.deepEqual(cut, [
    { kind: 'text', delta: 'We' },
    { kind: 'error', title: 'The reply stopped before its end.' },
  ]);
});

test('tst_mv9jyb Aborting the signal stops the reply as it comes', async () => {
  const leaving = new AbortController();
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(encoder.encode('event: text\ndata: {"delta":"We"}\n\n'));
      leaving.signal.addEventListener('abort', () => controller.error(leaving.signal.reason));
    },
  });
  const { desk, signals } = answering(body);
  const seen: string[] = [];
  await assert.rejects(
    (async () => {
      for await (const event of reply(desk, 'c1', 'Hello', leaving.signal)) {
        seen.push(event.kind);
        leaving.abort();
      }
    })(),
    { name: 'AbortError' },
  );
  assert.deepEqual(seen, ['text']);
  assert.equal(signals[0], leaving.signal);
});
