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
