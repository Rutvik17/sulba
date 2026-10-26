`errors.AsType[*StatusError](err)` finds a `*StatusError` however it's wrapped. `http.StatusTooManyRequests` is 429.

---

`fmt.Errorf("upstream %s: %w", upstream.Name(), err)` names the upstream and keeps its error for `Is` and `AsType`. Check `Retryable` on the wrapped error, which finds the same things.

---

`errors.Join(append(failures, err)...)` joins the errors so far with one more.
