Double the delay `n - 1` times, and stop at `Max`. Stop before you double, once the delay is half of `Max` or more, so a large `n` can't overflow.

---

`ctx.Deadline()` gives the deadline and whether there is one, and `time.Until(deadline)` how long is left.

---

`errors.Join(ctx.Err(), err)` gives both the caller's error and the call's.
