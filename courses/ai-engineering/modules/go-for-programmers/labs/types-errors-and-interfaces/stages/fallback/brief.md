A model can have more than one upstream: the desk's own server first, say, then a backup. When one fails, the next may answer. Each upstream is an `Upstream`, anything with a `Name` and a `Chat` method. The gateway's own, over HTTP, comes later, and the tests have their own. An upstream that answers with a status rather than a reply gives a `*StatusError`.

In `fallback.go`, write:

- `Retryable(err)`, which reports whether another upstream might answer where `err` came from: a `*StatusError` of 429, from an upstream that's busy, or of 500 or more, from one that's failing, or an error that wraps `context.DeadlineExceeded`, from one that ran out of time. Any other error, a 400 included, would come back the same from any upstream. It finds a `*StatusError` however it's wrapped.
- `Fallback(ctx, upstreams, request)`, which asks each upstream in turn and gives the first reply, with `Upstream` set to the name of the upstream that gave it:
  - each upstream's error is wrapped as `upstream NAME: ...`, with its name;
  - an error that isn't retryable stops it at once, and it gives that error;
  - when every upstream fails, it gives their errors joined;
  - before each upstream, it checks `ctx`: once the caller is done, it asks no more, and gives the errors so far joined with `ctx.Err()`;
  - with no upstreams, it gives `ErrNoUpstreams`.

```go
func Retryable(err error) bool
func Fallback(ctx context.Context, upstreams []Upstream, request ChatRequest) (Reply, error)
```

The test of a deadline runs in `synctest.Test`, whose clock moves only while the test waits, so a two-second deadline takes no time.
