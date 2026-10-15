"""Bootstrap estimates of how far a number measured on a sample could be off."""

import numpy as np


def resample(n, repeats, rng):
    """The row numbers of repeats resamples, each n rows drawn with replacement from 0 to
    n - 1, all drawn at once from rng."""
    raise NotImplementedError


def bootstrap_distribution(values, statistic, repeats, rng):
    """statistic over each of repeats resamples of values. statistic takes an axis, as
    np.mean does."""
    raise NotImplementedError


def standard_error(distribution):
    """The standard deviation of a bootstrap distribution, with n - 1 in its divisor."""
    raise NotImplementedError
