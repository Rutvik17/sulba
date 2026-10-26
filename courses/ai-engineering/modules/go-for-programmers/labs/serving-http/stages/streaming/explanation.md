Server-sent events are text, a field to a line. The WHATWG's HTML standard, which defines them, says how to read each line: "If the line is empty (a blank line) Dispatch the event", "If the line starts with a U+003A COLON character (:) Ignore the line", and for a `data` field, "Append the field value to the data buffer". The space after the colon is optional: its example of `data:test` and `data: test` "fires two identical events", because "the space after the colon is ignored if present." llama.cpp's server sends comments of its own, by default every 30 seconds, while a long prompt is read: its `sse_ping_interval` is the "Interval in seconds between SSE comment pings emitted while the stream stays silent". A reader that took every line for data would fail on the first one.

`bufio.Scanner` reads lines up to a limit, 64 kB by default (`MaxScanTokenSize = 64 * 1024`), and "Scanning stops unrecoverably at EOF, the first I/O error, or a token too large to fit in the Scanner.Buffer." A chunk is small, but the limit is set to a megabyte, as `Chat`'s is, so a long one doesn't end the stream.

A stream that ends without `[DONE]` was cut short: the model server crashed, or a proxy dropped the connection. `Stream` gives an error rather than the text so far, which would look like a whole reply.

The gateway's side has to push each piece out. A handler's writes wait in a buffer, and `ResponseController.Flush` "flushes buffered data to the client." Unlike a type assertion to `http.Flusher`, `http.NewResponseController(w)` also works through a writer that wraps the original, such as a middleware's, when it has an `Unwrap` method that gives the original.

Once the first piece is flushed, the status and headers are gone: "Changing the header map after a call to WriteHeader (or Write) has no effect". A failure before it can still be a 502 or a 429 from `WriteError`, with its `Retry-After`. A failure after it can only end the stream, and the missing `[DONE]` tells the caller the reply is incomplete.

When the caller hangs up, `r.Context()` is canceled, `Stream`'s request to the upstream stops, and the model server stops writing a reply no one will read.
