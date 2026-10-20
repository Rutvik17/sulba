"""Smaller copies of the help desk's vectors, for an index that takes less memory."""

import numpy as np


def shorten(vectors: np.ndarray, numbers: int) -> np.ndarray:
    """Each vector cut to its first numbers, as nomic-embed-text-v1.5's card cuts them:
    layer normalization across all its numbers, then the first numbers, then a length of
    1."""
    raise NotImplementedError


def bounds(vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The lowest and the highest value of each number across the vectors."""
    raise NotImplementedError


def quantize(vectors: np.ndarray, low: np.ndarray, high: np.ndarray) -> np.ndarray:
    """Each number as the nearest of 256 steps from its low, 0, to its high, 255, as
    uint8. A number past its bounds takes the step at the bound, and one whose bounds
    are equal 0."""
    raise NotImplementedError


def restore(codes: np.ndarray, low: np.ndarray, high: np.ndarray) -> np.ndarray:
    """The numbers the codes stand for, as float32."""
    raise NotImplementedError
