Each training step follows the gradient on one batch, and that gradient is a mean over the batch's records. How far it strays from the gradient over all the records comes down to how far a random batch's mean strays from the mean of all the records.

A random batch's mean is a random variable. Its expectation, its average over every batch that could be drawn, is the mean of all the records. Its variance, the expected square of how far it lands from that mean, is

```math
\frac{\sigma^2}{b} \cdot \frac{n - b}{n - 1}
```

for a batch of `$b$` rows drawn without replacement from `$n$` records, where `$\sigma^2$` is the variance of the values over all the records, `np.var(values)`.

Write `batch_mean_variance`, that variance. Then write `simulated_means`, the means of `repeats` batches drawn at random, each without replacement, to compare the formula with batches actually drawn.

```
batch_mean_variance(values, size) -> a number
simulated_means(values, size, rng, repeats) -> an array of repeats means
```

The tests compare your variance with SciPy's `scipy.stats.hypergeom`, the distribution of the number of malignant records in a batch drawn without replacement, and with your simulation, for the share malignant and for the worst area.
