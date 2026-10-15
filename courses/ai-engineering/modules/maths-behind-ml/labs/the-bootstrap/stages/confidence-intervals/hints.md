`np.quantile(distribution, [tail, 1 - tail])`, with `tail = (1 - confidence) / 2`, gives both ends in one call.

---

`basic_interval` can take the two quantiles from `percentile_interval` and reflect them: the high quantile gives the low end.
