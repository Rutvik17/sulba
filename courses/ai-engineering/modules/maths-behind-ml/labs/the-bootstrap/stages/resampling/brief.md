The clinic's simplest rule calls a sample malignant when it is nearer the malignant records' mean than the benign ones', with each measurement standardized. It gets {% $fig.right %} of the {% $fig.new %} new samples right, an accuracy of {% $fig.accuracy %}. Another {% $fig.new %} samples would give another number, and the clinic needs to know how far this one could be off. The bootstrap answers from the one sample there is: it draws resamples of it, each {% $fig.new %} samples drawn with replacement, and measures the accuracy on every one.

Start `bootstrap.py`. Write `resample`, the row numbers of `repeats` resamples, all drawn at once with `rng.integers(0, n, (repeats, n))`, as SciPy's `scipy.stats.bootstrap` draws them, so that the same seed gives the same resamples. Then write `bootstrap_distribution`, a statistic over each resample. `statistic` takes an `axis`, as `np.mean` and `np.median` do, so one call works out every resample's value from an array with a row for each. Then write `standard_error`, the standard deviation of a bootstrap distribution, with `n - 1` in its divisor, as SciPy's is.

```
resample(n, repeats, rng) -> an array of repeats rows of n row numbers
bootstrap_distribution(values, statistic, repeats, rng) -> an array of repeats values
standard_error(distribution) -> a number
```

The tests compare your distributions and standard error with SciPy's `bootstrap`, for the clinic's accuracy and for the median of the new samples' worst area.
