"""Two searches compared question by question: how sure a difference is."""

import numpy as np


def randomization_test(
    a: np.ndarray, b: np.ndarray, repeats: int, rng: np.random.Generator
) -> float:
    """The two-sided p-value of the difference between a's mean and b's, with each
    question's two values swapped where `rng.integers(0, 2, size=(repeats, len(a)))` gives
    1: the share of the resamples, the observed difference among them, at least as far from
    0 as the observed difference."""
    differences = a - b
    observed = abs(differences.mean())
    signs = 1 - 2 * rng.integers(0, 2, size=(repeats, len(a)))
    resampled = np.abs((signs * differences).mean(axis=1))
    return float((1 + np.count_nonzero(resampled >= observed)) / (1 + repeats))


def bootstrap_interval(
    a: np.ndarray,
    b: np.ndarray,
    confidence: float,
    repeats: int,
    rng: np.random.Generator,
) -> tuple[float, float]:
    """The percentile interval of the difference between a's mean and b's, from the
    questions resampled in pairs, as `rng.integers(0, len(a), size=(repeats, len(a)))`
    draws them."""
    rows = rng.integers(0, len(a), size=(repeats, len(a)))
    differences = a[rows].mean(axis=1) - b[rows].mean(axis=1)
    low, high = np.quantile(differences, [(1 - confidence) / 2, (1 + confidence) / 2])
    return float(low), float(high)
