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
    raise NotImplementedError


def unpaired(
    baseline: np.ndarray, candidate: np.ndarray, pages: list[str], confidence: float
) -> Change:
    """The change from each release's score and standard error alone, as if the two had
    answered different questions."""
    raise NotImplementedError
