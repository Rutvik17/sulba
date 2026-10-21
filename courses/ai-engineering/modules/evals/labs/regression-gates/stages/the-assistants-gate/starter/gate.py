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
    return float(values.std(ddof=1) / math.sqrt(len(values)))


def gate(
    baseline: np.ndarray, candidate: np.ndarray, pages: list[str], alpha: float
) -> Verdict:
    """Compares the candidate's scores with the baseline's on the same questions, a row
    for each question and a column for each sample, and stops the candidate when its
    score is lower at level alpha."""
    before = baseline[:, 0]
    after = candidate[:, 0]
    change = float(after.mean() - before.mean())
    error = math.hypot(spread(before, pages), spread(after, pages))
    z = NormalDist().inv_cdf(1 - alpha)
    low, high = change - z * error, change + z * error
    return Verdict(change=change, low=low, high=high, ships=change >= 0)
