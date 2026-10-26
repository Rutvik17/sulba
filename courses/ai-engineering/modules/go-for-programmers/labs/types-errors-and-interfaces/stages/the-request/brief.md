The help desk's assistants call their models through a gateway: one service that takes each chat request, sends it to a model server that can answer, and counts what each key uses. You write it in Go, starting with the request.

In `request.go`, `DecodeRequest(r, limit)` reads one chat request from `r`, as JSON, and checks it:

- In JSON, a `ChatRequest`'s fields are `model`, `messages`, `max_tokens` and `stream`, and a `Message`'s are `role` and `content`. Give the fields those names with struct tags.
- A body that isn't one JSON object gives an error that wraps `ErrNotJSON` and json's own error, so a caller can find either. Anything after the object counts too.
- A value of the wrong type, such as `"max_tokens": "lots"`, gives a `*FieldError` for its field, named as json names it, such as `messages.0.content`.
- No model gives `ErrNoModel`, and no messages gives `ErrNoMessages`.
- A message's role is `system`, `user` or `assistant`. Any other gives a `*FieldError` for `messages.N.role`, whose message says the role it got.
- `max_tokens` can't be below 0 or over `limit`: each gives a `*FieldError` for `max_tokens`, and over the limit, its message gives the limit. A request that asks for none gets `limit`.

```go
func DecodeRequest(r io.Reader, limit int) (ChatRequest, error)
```

The tests decode their requests with a limit of 1024.
