A channel with a buffer of `n` holds a place for each call: a send takes one, and waits while all `n` are taken, and a receive frees one. `len` of the channel is how many are taken.

---

`defer func() { <-g.slots }()` frees the place however `call` ends, a panic included.

---

`sync.WaitGroup`'s `Go` runs a function in a new goroutine and `Wait` waits for them all. `context.WithCancelCause` gives a cancel that keeps the first error it's given, which `context.Cause(ctx)` gives back.
