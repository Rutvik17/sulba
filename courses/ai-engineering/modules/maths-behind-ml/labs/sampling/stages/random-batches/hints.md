`rng.permutation(n)` gives the row numbers 0 to `n - 1` in a random order.

---

Slice that order in steps of `size`: `order[start : start + size]` for each `start` in `range(0, n, size)`. The last slice stops at the end of the order by itself. `values[batch]` keeps a batch's rows, and `np.mean(..., axis=0)` averages them, a number or a row at a time.
