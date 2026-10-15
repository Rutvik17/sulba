A standard error says how far the accuracy could be off. An interval says where the true accuracy could be. A 95% confidence interval is made by a method that covers the true value for 95% of the samples it could be given.

Write `percentile_interval`, the simplest bootstrap interval: the quantiles of the bootstrap distribution that leave `(1 - confidence) / 2` of it outside on each side. Then write `basic_interval`, which reflects that interval about the estimate, the statistic on the whole sample: from `2 * estimate - high` to `2 * estimate - low`.

```
percentile_interval(distribution, confidence) -> (low, high)
basic_interval(estimate, distribution, confidence) -> (low, high)
```

The tests compare your intervals with SciPy's `bootstrap`, with its `method` set to `"percentile"` and to `"basic"`.
