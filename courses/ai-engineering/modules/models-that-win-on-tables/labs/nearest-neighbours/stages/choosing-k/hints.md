`sort_beans` is `scale`, then `nearest`, then `vote`.

---

A bean's `k` nearest are the first `k` of its `max(ks)` nearest, so one call to `nearest` serves every `k`: `vote(varieties, neighbours[:, :k])`.
