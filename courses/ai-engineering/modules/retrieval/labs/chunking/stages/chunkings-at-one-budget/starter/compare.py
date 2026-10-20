"""Chunkings compared by a search through each: the chunks most similar to a question,
taken until a budget of words, scored by the characters of its answer they hold."""

import numpy as np

from score import Place, iou, precision, recall


def ranked(question: np.ndarray, vectors: np.ndarray) -> np.ndarray:
    """The rows of vectors, the most similar to the question first: by the dot product
    of their whole numbers, a tie going to the earlier row."""
    raise NotImplementedError


def within(order: np.ndarray, words: list[int], budget: int) -> list[int]:
    """The rows in order, until the next would take their words past budget."""
    raise NotImplementedError


def compared(
    questions: np.ndarray,
    answers: list[list[Place]],
    places: list[Place],
    vectors: np.ndarray,
    words: list[int],
    budget: int,
) -> tuple[float, float, float]:
    """The mean recall, precision and IoU over the questions of a search through the
    chunks: for each question, the chunks most similar to it, taken until budget
    words."""
    raise NotImplementedError
