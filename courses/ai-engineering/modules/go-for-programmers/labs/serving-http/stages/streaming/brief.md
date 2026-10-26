A model takes seconds to write a reply of a few hundred tokens. Streamed, the caller sees it start at once. llama.cpp's server and OpenAI's API stream as server-sent events: each event a `data:` line with a chunk of JSON, ended by a blank line, and `data: [DONE]` at the end.

In `stream.go`, write:

- `upstream.Stream(ctx, request, each)`, which posts `request` with `Stream` set and `Accept: text/event-stream`, then reads the answer's events as they arrive, and calls `each` with each chunk's `delta` content that isn't empty. It:
  - reads a `data` field with or without a space after its colon, and skips comments, the lines that start with a colon, and every other field;
  - stops at the first error `each` gives, and gives it;
  - gives the reply, with the whole text, at `[DONE]`, and an error for a stream that ends before it;
  - gives a `*StatusError` for an answer that isn't 200, as `Chat` does.
- `Relay(w, r, upstream, request)`, which answers a caller who asked to stream: `Content-Type: text/event-stream` and `Cache-Control: no-cache`, then a `Chunk` for each piece, with the object `chat.completion.chunk`, flushed as it's written, then `data: [DONE]`. A failure before the first piece is answered with `WriteError`. A failure after it ends the stream without `[DONE]`. `Relay` gives the error.

```go
func (u *HTTPUpstream) Stream(ctx context.Context, request ChatRequest, each func(piece string) error) (Reply, error)
func Relay(w http.ResponseWriter, r *http.Request, upstream *HTTPUpstream, request ChatRequest) error
```

`stream.go` has the `Chunk`, `ChunkChoice` and `Delta` types. The tests' model servers wait between pieces, so a piece the gateway holds back shows.
