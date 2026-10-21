"""How well a grader's verdicts agree with people's labels."""

import numpy as np


def accuracy(labels: np.ndarray, verdicts: np.ndarray) -> float:
    """The share of the replies the grader gives the people's label."""
    raise NotImplementedError


def kappa(labels: np.ndarray, verdicts: np.ndarray) -> float:
    """Cohen's kappa: how far the agreement goes past the agreement the two would reach by
    chance, with each giving 1 at its own rate, as a share of the most it could go."""
    raise NotImplementedError


def auc(labels: np.ndarray, scores: np.ndarray) -> float:
    """The chance that a reply labelled 1 scores above one labelled 0, a tie counting half."""
    raise NotImplementedError


def best_threshold(labels: np.ndarray, scores: np.ndarray) -> float:
    """The score at or above which a reply is given 1 that gives the highest kappa, the
    lowest such score if several do."""
    raise NotImplementedError
