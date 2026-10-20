"""How far a test set's mean score could be from the mean over every question it was drawn
from."""

from statistics import NormalDist

import numpy as np


def standard_error(scores: np.ndarray) -> float:
    """The standard error of the mean of independent scores."""
    raise NotImplementedError


def clustered_standard_error(scores: np.ndarray, clusters: list[str]) -> float:
    """The standard error of the mean of scores drawn in clusters, each cluster's scores
    counted together."""
    raise NotImplementedError


def margin(standard_error: float, confidence: float) -> float:
    """The margin of error: how far the interval at this confidence reaches each side of the
    mean."""
    raise NotImplementedError
