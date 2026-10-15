Percentile intervals fell short on small, skewed samples. The bias-corrected and accelerated interval, BCa, is the one SciPy's `bootstrap` gives unless told otherwise. It keeps the percentile interval's idea, but moves its two quantile levels to make up for two things.

The bias correction: when the estimate sits off the middle of the bootstrap distribution, the share of resamples below it, counting a tie as half, isn't 0.5. Its standard normal quantile is `$z_0$`, which is 0 when the estimate sits in the middle.

The acceleration: a measure of how skewed the statistic is, read off the jackknife. Leave out each of the `$n$` values in turn, and work out the statistic on the `$n - 1$` left, `$\hat\theta_{(i)}$`. With `$\hat\theta_{(\cdot)}$` their mean and `$u_i = (n - 1)(\hat\theta_{(\cdot)} - \hat\theta_{(i)})$`,

```math
a = \frac{\sum_i u_i^3}{6 \left(\sum_i u_i^2\right)^{3/2}}
```

The interval's ends are then the bootstrap distribution's quantiles at

```math
\Phi\left(z_0 + \frac{z_0 + z}{1 - a(z_0 + z)}\right)
```

where `$\Phi$` is the standard normal distribution function, and `$z$` its quantile at `(1 - confidence) / 2` for the low end and at `(1 + confidence) / 2` for the high end. With `$z_0 = a = 0$`, they are the percentile interval's.

Write `bca_interval`, the BCa interval for `statistic` over `values`, from their bootstrap `distribution`.

```
bca_interval(values, statistic, distribution, confidence) -> (low, high)
```

`scipy.stats.norm.ppf` gives standard normal quantiles, and `norm.cdf` gives `$\Phi$`. The tests compare your intervals with SciPy's `bootstrap`, whose `method` is `"BCa"` unless told otherwise.
