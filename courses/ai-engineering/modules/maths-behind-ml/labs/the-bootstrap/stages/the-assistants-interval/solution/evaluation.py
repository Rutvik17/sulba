"""An interval for the clinic's accuracy on its new samples."""

import numpy as np


def resample(n, repeats, rng):
    """The row numbers of repeats resamples of n rows, drawn with replacement."""
    return rng.integers(0, n, (repeats, n))


def resampled_accuracies(predictions, labels, repeats, seed):
    """The accuracy of predictions against labels on each of repeats resamples."""
    rows = resample(len(labels), repeats, np.random.default_rng(seed))
    return np.mean(predictions[rows] == labels[rows], axis=1)


def percentile_interval(accuracies, confidence):
    """The quantiles of the accuracies that leave (1 - confidence) / 2 outside on each
    side."""
    low, high = np.quantile(accuracies, [(1 - confidence) / 2, (1 + confidence) / 2])
    return float(low), float(high)


def basic_interval(estimate, accuracies, confidence):
    """The percentile interval reflected about the estimate."""
    low, high = percentile_interval(accuracies, confidence)
    return 2 * estimate - high, 2 * estimate - low
