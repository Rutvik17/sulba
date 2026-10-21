"""How far a candidate release's score is from the baseline's on the same questions."""

import math
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np

from samples import standard_error


@dataclass(frozen=True)
class Change:
    """The candidate's score less the baseline's, and its margin of error."""

    change: float
    margin: float


def paired(
    baseline: np.ndarray, candidate: np.ndarray, pages: list[str], confidence: float
) -> Change:
    """The change from each question's difference between the two releases' means, each
    page's questions counted together."""
    differences = candidate.mean(axis=1) - baseline.mean(axis=1)
    error = standard_error(differences[:, None], pages)
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    return Change(change=float(differences.mean()), margin=z * error)


def unpaired(
    baseline: np.ndarray, candidate: np.ndarray, pages: list[str], confidence: float
) -> Change:
    """The change from each release's score and standard error alone, as if the two had
    answered different questions."""
    change = float(candidate.mean(axis=1).mean() - baseline.mean(axis=1).mean())
    error = math.hypot(
        standard_error(baseline, pages), standard_error(candidate, pages)
    )
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    return Change(change=change, margin=z * error)
