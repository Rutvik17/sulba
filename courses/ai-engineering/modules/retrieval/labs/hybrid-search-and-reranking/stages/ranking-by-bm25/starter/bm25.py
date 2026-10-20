"""The help desk's passages ranked for a question by BM25: each of the question's words
weighted by how few passages hold it, by how often a passage holds it, the count leveling
off, and by how long the passage is."""

import numpy as np

K1 = 1.5
B = 0.75


def words(text: str) -> list[str]:
    """A text's words: its runs of letters, digits and underscores, lowercased."""
    raise NotImplementedError


class BM25:
    """An index of passages, each given as its words."""

    def __init__(self, passages: list[list[str]]) -> None:
        raise NotImplementedError

    def scores(self, question: list[str]) -> np.ndarray:
        """Each passage's score for the question's words, a word counted as many times as the
        question holds it."""
        raise NotImplementedError

    def top(self, question: list[str], k: int) -> list[int]:
        """The rows of the k passages with the highest scores, a tie going to the earlier
        passage."""
        raise NotImplementedError
