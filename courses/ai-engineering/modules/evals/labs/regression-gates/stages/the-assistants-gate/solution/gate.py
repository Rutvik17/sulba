"""The help desk's release gate: stops a candidate release whose score drops."""

import math
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np


@dataclass(frozen=True)
class Verdict:
    """The candidate's change in score, the interval around it, and whether it ships."""

    change: float
    low: float
    high: float
    ships: bool


def spread(values: np.ndarray, pages: list[str]) -> float:
    """The standard error of the values' mean."""
    sums: dict[str, float] = {}
    for page, residual in zip(pages, values - values.mean(), strict=True):
        sums[page] = sums.get(page, 0.0) + float(residual)
    groups = len(sums)
    total = sum(value**2 for value in sums.values())
    return math.sqrt(groups / (groups - 1) * total) / len(values)


def gate(
    baseline: np.ndarray, candidate: np.ndarray, pages: list[str], alpha: float
) -> Verdict:
    """Compares the candidate's scores with the baseline's on the same questions, a row
    for each question and a column for each sample, and stops the candidate when its
    score is lower at level alpha."""
    before = baseline.mean(axis=1)
    after = candidate.mean(axis=1)
    change = float(after.mean() - before.mean())
    error = spread(after - before, pages)
    z = NormalDist().inv_cdf(1 - alpha)
    low, high = change - z * error, change + z * error
    return Verdict(change=change, low=low, high=high, ships=high >= 0)
