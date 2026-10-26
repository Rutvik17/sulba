So far the gateway's upstreams have been stand-ins. An `HTTPUpstream` is a real one: a model server with an API like OpenAI's, such as llama.cpp's server, which the gateway asks over HTTP.

In `upstream.go`, write:

- `NewHTTPUpstream(name, baseURL, client)`, the upstream called `name` at `baseURL`, given with or without a slash at its end, asked through `client`.
- `upstream.Chat(ctx, request)`, which posts `request` as JSON to `/v1/chat/completions` at its address, with `ctx`, and gives the reply's text and its tokens from the answer, a `ChatResponse`. It reads no more than a megabyte of a reply, and gives an error for one that isn't JSON or has no choices.
- An answer that isn't 200 gives a `*StatusError`: its status, what it said, the message of an `ErrorBody` or else its text, reading no more than 4 kB, and the seconds of its `Retry-After` as `RetryAfter`.
- It closes the body of every answer.

```go
func NewHTTPUpstream(name, baseURL string, client *http.Client) *HTTPUpstream
func (u *HTTPUpstream) Name() string
func (u *HTTPUpstream) Chat(ctx context.Context, request ChatRequest) (Reply, error)
```

An `*HTTPUpstream` is an `Upstream`, so `Fallback` and your server can ask it. The tests start model servers of their own with `httptest`.
