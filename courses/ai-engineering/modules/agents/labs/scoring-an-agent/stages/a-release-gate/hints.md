`trials(runs, variant)` from your `scores.py` gives each task's `(n, c)`, and `pass_hat_k(n, c, k)` each task's pass^k.

---

`per_task(runs, variant, "seconds")` from your `costs.py` gives each task's median, and `quantile` and `interval` the percentile and its ends.

---

`math.nan <= 180` and `math.nan > 180` are both `False`.
