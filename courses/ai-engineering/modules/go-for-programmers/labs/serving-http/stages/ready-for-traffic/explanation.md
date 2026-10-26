An `http.Server`'s timeouts are off until they're set: of each, "A zero or negative value means there will be no timeout." A client that sends its headers a byte at a time, or opens a connection and never sends anything, holds a connection and its goroutine for as long as it likes. Filippo Valsorda's 2016 guide to net/http's timeouts, on Cloudflare's blog: "Otherwise very slow or disappearing clients might leak file descriptors", until the server's accept fails with "too many open files". It adds that `http.ListenAndServe` and its like "are unfit for public Internet servers", since they leave every timeout off.

The four timeouts cover different parts of a request. `ReadHeaderTimeout` is "the amount of time allowed to read request headers", and `ReadTimeout` "the maximum duration for reading the entire request, including the body". The docs say "most users will prefer to use ReadHeaderTimeout. It is valid to use them both", and the gateway does, since its bodies are small. `WriteTimeout` "is reset whenever a new request's header is read", so it bounds the request's whole reply: 5 minutes leaves room for a long stream, and a handler that needs longer can move its own deadline with `ResponseController.SetWriteDeadline`. `IdleTimeout` is "the maximum amount of time to wait for the next request when keep-alives are enabled".

`Shutdown` "works by first closing all open listeners, then closing all idle connections, and then waiting indefinitely for connections to return to idle and then shut down." Two of its rules shape `Run`. "When Shutdown is called, Serve, ServeTLS, ListenAndServe, and ListenAndServeTLS immediately return ErrServerClosed. Make sure the program doesn't exit and waits instead for Shutdown to return." And "If the provided context expires before the shutdown is complete, Shutdown returns the context's error". `ctx` is already done, so `Run` gives `Shutdown` a context of its own: `context.WithoutCancel` "returns a derived context that points to the parent context and is not canceled when parent is canceled", and `WithTimeout` gives it the grace. Once the grace is up, `Close` "immediately closes all active net.Listeners and any connections in state StateNew, StateActive, or StateIdle".

Kubernetes is where the grace comes from. Its docs: "A Pod is granted a term to terminate gracefully, which defaults to 30 seconds", "The kubelet triggers the container runtime to send a TERM signal to process 1 inside each container", and "Once the grace period has expired, the KILL signal is sent to any remaining processes". A grace of 25 seconds leaves `Run` time to close what's left and return before the kill. `main` turns the signal into a context with `signal.NotifyContext`, which gives "a copy of the parent context that is marked done (its Done channel is closed) when one of the listed signals arrives". With the gateway's `Server` in `server`, `main` is a few lines:

```go
ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
defer stop()
listener, err := net.Listen("tcp", ":8080")
if err != nil {
	log.Fatal(err)
}
if err := gateway.Run(ctx, gateway.NewHTTPServer(server.Handler()), listener, 25*time.Second); err != nil {
	log.Fatal(err)
}
```
