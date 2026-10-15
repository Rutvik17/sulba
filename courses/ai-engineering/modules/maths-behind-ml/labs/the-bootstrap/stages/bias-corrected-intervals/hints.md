`(np.sum(distribution < estimate) + np.sum(distribution <= estimate)) / (2 * len(distribution))` is the share of resamples below the estimate, counting a tie as half. `norm.ppf` of it is `$z_0$`.

---

`np.tile(values, (n, 1))` has a row of all the values for each one, and `~np.eye(n, dtype=bool)` marks every entry off the diagonal. Indexing the first with the second, and reshaping to `(n, n - 1)`, gives a row for each value left out, and `statistic(..., axis=-1)` works out each row's.

---

Work out both levels, then `np.quantile(distribution, levels)` gives both ends.
