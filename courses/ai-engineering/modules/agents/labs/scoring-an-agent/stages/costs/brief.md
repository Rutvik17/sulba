A run costs seconds and tokens, and some tasks cost far more than others. An average over the runs hides that spread; percentiles show it: the median for a typical task, and the 90th percentile for the slow tenth. Each needs an interval, as a score does.

A task's trials aren't independent draws, since a task that's slow once tends to be slow every time, so each task counts once, by its median over its trials.

In `costs.py`, `cost(run, measure)` gives a run's `"seconds"` or `"tokens"` from a row of `runs.csv`. Write:

- `per_task(runs, variant, measure)`, each task's median of the measure over the variant's trials of it.
- `quantile(values, p)`, the p-quantile of the values as NumPy's `quantile` gives it by default: in the values sorted, at position `$(n - 1)p$`, counting from 0, between the two values on either side, in proportion.
- `binomial_cdf(k, n, p)`, the chance of at most k successes in n trials, each a success with the chance p: `$\sum_{i=0}^{k} \binom{n}{i} p^i (1 - p)^{n - i}$`.
- `interval(values, p, confidence=0.95)`, the interval for the p-quantile that SciPy's `quantile_test` gives, with `$a = (1 - \text{confidence}) / 2$`. Its low end is the value at index j - 1 of the values sorted, j the least count from 0 to n with `binomial_cdf(j, n, p)` at least a. Its high end is the value at index k, k the least count with `1 - binomial_cdf(k, n, p)` at most a. An end whose index is outside the values is `math.nan`.

The tests compare your quantiles and intervals with NumPy's and SciPy's on {% $fig.cases %} recorded cases in `references/quantiles.json`.

```
per_task(runs, variant, measure) -> dict[str, float]
quantile(values, p) -> float
binomial_cdf(k, n, p) -> float
interval(values, p, confidence=0.95) -> tuple[float, float]
```
