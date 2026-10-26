Run `server.Serve(listener)` in a goroutine that sends its error on a channel with room for one, then `select` on that channel and `ctx.Done()`.

---

`ctx` is done by the time you shut down, and a `Shutdown` given a done context gives up at once. `context.WithTimeout(context.WithoutCancel(ctx), grace)` gives a context with the grace's deadline and none of `ctx`'s cancellation.
