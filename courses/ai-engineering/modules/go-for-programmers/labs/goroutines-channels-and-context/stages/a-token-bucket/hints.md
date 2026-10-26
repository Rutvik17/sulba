Keep the tokens as a `float64` and the time of the last refill. Each `Allow` adds what the time since then has earned, `elapsed.Seconds() * rate`, up to the burst, and sets the time to now.

---

`b.mu.Lock()` then `defer b.mu.Unlock()` holds the lock until the method returns, whichever way it does.

---

In `Wait`, work out how long the next token takes, unlock, then wait in a `select` on `ctx.Done()` and a `time.NewTimer`'s channel. When the timer fires, lock again and look: another caller may have taken the token.
