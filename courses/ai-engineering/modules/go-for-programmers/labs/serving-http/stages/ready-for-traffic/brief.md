Before the gateway takes traffic from the internet, its server needs limits on slow clients, and a way to stop that doesn't cut off the requests in flight. Each deploy stops the gateway's process: Kubernetes, for one, sends it `SIGTERM`, and by default kills it 30 seconds later if it's still running.

In `serve.go`, write:

- `NewHTTPServer(handler)`, an `*http.Server` for `handler` that reads a request's headers within 5 seconds and the whole request within 30, gives a reply 5 minutes to write, enough to stream a long one, and closes a connection left idle for 2 minutes.
- `Run(ctx, server, listener, grace)`, which serves on `listener` until `ctx` is done, then shuts the server down: it stops taking connections, waits up to `grace` for the requests in flight, and then closes the connections still open. It gives:
  - `nil` after a shutdown that finished in time;
  - the shutdown's error, wrapped, once the grace is up;
  - `Serve`'s error, at once, if the server stops serving by itself.

```go
func NewHTTPServer(handler http.Handler) *http.Server
func Run(ctx context.Context, server *http.Server, listener net.Listener, grace time.Duration) error
```

The gateway's `main` gives `Run` a context that's done when the process gets `SIGTERM` or an interrupt, and a grace of 25 seconds, inside Kubernetes's 30.

The tests show you which of their cases pass, but not what they gave or expected. Checks then shut a server down with requests in flight, before it ships.
