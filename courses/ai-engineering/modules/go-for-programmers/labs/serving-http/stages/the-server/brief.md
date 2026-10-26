The gateway's parts can read a request, route it, fall back along its route, limit each key and answer a failure. A `Server` puts them behind HTTP, at the path OpenAI's API uses, so a client built for that API can call the gateway.

In `server.go`, write `server.Handler()`, which gives an `http.Handler` with two routes:

- `GET /healthz`, which answers `ok`.
- `POST /v1/chat/completions`, which, in this order:
  - refuses a request without `Authorization: Bearer KEY`, for a key in `Keys`, with 401 and `WWW-Authenticate: Bearer realm="gateway"`;
  - refuses a key over its rate limit, when `Limiter` is set, with 429 and `Retry-After: 1`;
  - reads the request with `DecodeRequest` and `MaxTokens`, and refuses a body over `MaxBody` bytes with 413;
  - answers what `DecodeRequest` and `routes.For` refuse with `WriteError`, as it does a route that names an upstream not in `Upstreams`;
  - asks the route's upstreams with `Fallback`, passing it the request's context, and answers with the reply as a `ChatResponse`, with the name of the upstream that gave it in `X-Upstream`.

Its own refusals, the 401, 429 and 413, are an `ErrorBody` of the type `unauthorized`, `rate_limited` or `too_large`.

```go
func (s *Server) Handler() http.Handler
```

`server.go` has the `Server`, `ChatResponse`, `Choice` and `Tokens` types. The tests call the handler through `httptest`, with upstreams that answer at once.
