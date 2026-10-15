"""Bootstrap estimates of how far a number measured on a sample could be off."""

import numpy as np


def resample(n, repeats, rng):
    """The row numbers of repeats resamples, each n rows drawn with replacement from 0 to
    n - 1, all drawn at once from rng."""
    return rng.integers(0, n, (repeats, n))


def bootstrap_distribution(values, statistic, repeats, rng):
    """statistic over each of repeats resamples of values. statistic takes an axis, as
    np.mean does."""
    return statistic(values[resample(len(values), repeats, rng)], axis=-1)


def standard_error(distribution):
    """The standard deviation of a bootstrap distribution, with n - 1 in its divisor."""
    return float(np.std(distribution, ddof=1))


def percentile_interval(distribution, confidence):
    """The low and high ends of the interval between the distribution's quantiles that leave
    (1 - confidence) / 2 of it outside on each side."""
    tail = (1 - confidence) / 2
    low, high = np.quantile(distribution, [tail, 1 - tail])
    return float(low), float(high)


def basic_interval(estimate, distribution, confidence):
    """The percentile interval reflected about the estimate: 2 * estimate minus its high
    end, and 2 * estimate minus its low end."""
    low, high = percentile_interval(distribution, confidence)
    return 2 * estimate - high, 2 * estimate - low
