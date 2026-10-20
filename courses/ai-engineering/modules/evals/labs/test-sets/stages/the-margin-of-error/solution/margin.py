"""How far a test set's mean score could be from the mean over every question it was drawn
from."""

from statistics import NormalDist

import numpy as np


def standard_error(scores: np.ndarray) -> float:
    """The standard error of the mean of independent scores."""
    return float(np.sqrt(scores.var(ddof=1) / len(scores)))


def clustered_standard_error(scores: np.ndarray, clusters: list[str]) -> float:
    """The standard error of the mean of scores drawn in clusters, each cluster's scores
    counted together."""
    residuals = scores - scores.mean()
    sums: dict[str, float] = {}
    for cluster, residual in zip(clusters, residuals, strict=True):
        sums[cluster] = sums.get(cluster, 0.0) + float(residual)
    groups = len(sums)
    spread = sum(total**2 for total in sums.values())
    return float(np.sqrt(groups / (groups - 1) * spread) / len(scores))


def margin(standard_error: float, confidence: float) -> float:
    """The margin of error: how far the interval at this confidence reaches each side of the
    mean."""
    return NormalDist().inv_cdf((1 + confidence) / 2) * standard_error
