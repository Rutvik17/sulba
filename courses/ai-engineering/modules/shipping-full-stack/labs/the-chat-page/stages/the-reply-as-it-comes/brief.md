The desk sends its reply as server-sent events: `text` events with each piece, `tool` events as it uses its tools, then `done` with the whole reply or `error` with a title. The browser's `EventSource` reads such a stream, but it takes only an address and `withCredentials`, so it can't post the caller's message. The page reads the stream from `fetch`'s body instead. In `stream.ts`, write:

- `events(body)`, which gives each event of an event stream as its bytes arrive: its `type`, `message` unless an `event` field names another, and its `data`. It reads the stream as the HTML Standard says a browser does:
  - The bytes are UTF-8, and a byte order mark at the start is left out. A character's bytes can arrive in two chunks.
  - A line ends at a CRLF, an LF or a CR, and a CRLF can arrive split between two chunks.
  - A blank line gives the event, if it has data. Each `data` field adds its value and a line feed, and the last line feed goes.
  - A line that starts with a colon is a comment. A field without a colon has the whole line as its name and no value. One space after the colon is left out.
  - Fields other than `event` and `data` change nothing here, and an event the stream ends in the middle of isn't given.
  - When the caller stops reading early, `events` cancels the stream, so the connection is let go.
- `reply(desk, id, content, signal)`, which sends the message with your `desk.say` and gives the reply's events, each event's data read as JSON: `{ kind: 'text', delta }`, `{ kind: 'tool', name }`, then `{ kind: 'done', content }` or `{ kind: 'error', title }`, where it ends. A stream that ends before either gives `{ kind: 'error', title: 'The reply stopped before its end.' }`. Aborting the `signal` stops the reply where it is, with the `AbortError` it causes.

```ts
events(body: ReadableStream<Uint8Array>): AsyncGenerator<StreamEvent>
reply(desk: Desk, id: string, content: string, signal?: AbortSignal): AsyncGenerator<ReplyEvent>
```
