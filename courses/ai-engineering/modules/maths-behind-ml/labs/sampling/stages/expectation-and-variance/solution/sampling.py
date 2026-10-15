"""Random samples of the clinic's records, for training and checking."""

import numpy as np


def shuffled_batches(n, size, rng):
    """One epoch's batches: the row numbers 0 to n - 1 in a random order from rng, cut
    into batches of size rows, the last one smaller when size doesn't divide n."""
    order = rng.permutation(n)
    return [order[start : start + size] for start in range(0, n, size)]


def batch_mean(values, batch):
    """The mean of values over the rows in batch."""
    return np.mean(values[batch], axis=0)


def batch_mean_variance(values, size):
    """The variance of the mean of values over a random batch of size rows, drawn without
    replacement."""
    n = len(values)
    return float(np.var(values) / size * (n - size) / (n - 1))


def simulated_means(values, size, rng, repeats):
    """The means of values over repeats random batches of size rows, each drawn without
    replacement with rng."""
    n = len(values)
    return np.array(
        [np.mean(values[rng.choice(n, size, replace=False)]) for _ in range(repeats)]
    )
