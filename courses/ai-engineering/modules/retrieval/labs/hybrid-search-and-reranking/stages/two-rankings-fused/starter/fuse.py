"""Two rankings of the help desk's passages, by BM25 and by the vectors, fused into one by
reciprocal rank fusion, and each ranking's recall."""

import numpy as np


def nearest(question: np.ndarray, vectors: np.ndarray) -> np.ndarray:
    """The rows of vectors, the most similar to the question first: by the dot product of
    their whole numbers, a tie going to the earlier row."""
    raise NotImplementedError


def fused(rankings: list[np.ndarray], k: int = 60) -> np.ndarray:
    """The rows of every ranking, by the sum over the rankings of 1 / (k + the row's rank),
    the first rank being 1, a tie going to the earlier row."""
    raise NotImplementedError


def recall(rankings: list[np.ndarray], relevant: list[set[int]], k: int) -> float:
    """The share of the questions, each with its ranking and its relevant rows, that have a
    relevant row among the first k."""
    raise NotImplementedError
