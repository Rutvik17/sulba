"""The help desk's passages ranked for a question by BM25: each of the question's words
weighted by how few passages hold it, by how often a passage holds it, the count leveling
off, and by how long the passage is."""

import math
import re
from collections import Counter

import numpy as np

WORD = re.compile(r"\w+")
K1 = 1.5
B = 0.75


def words(text: str) -> list[str]:
    """A text's words: its runs of letters, digits and underscores, lowercased."""
    return WORD.findall(text.lower())


class BM25:
    """An index of passages, each given as its words."""

    def __init__(self, passages: list[list[str]]) -> None:
        self.count = len(passages)
        lengths = np.array([len(passage) for passage in passages], dtype=np.float64)
        # How much of a word's count each passage's length takes away.
        self.length = K1 * (1 - B + B * lengths / lengths.mean())
        held: dict[str, dict[int, int]] = {}
        for row, passage in enumerate(passages):
            for word, times in Counter(passage).items():
                held.setdefault(word, {})[row] = times
        # Each word's passages, and how many times each holds it.
        self.postings = {
            word: (
                np.fromiter(rows, dtype=np.int64),
                np.fromiter(rows.values(), dtype=np.float64),
            )
            for word, rows in held.items()
        }
        self.idf = {
            word: math.log(1 + (self.count - len(rows) + 0.5) / (len(rows) + 0.5))
            for word, rows in held.items()
        }

    def scores(self, question: list[str]) -> np.ndarray:
        """Each passage's score for the question's words, a word counted as many times as the
        question holds it."""
        total = np.zeros(self.count)
        for word in question:
            if word in self.postings:
                rows, tf = self.postings[word]
                total[rows] += self.idf[word] * tf / (tf + self.length[rows])
        return total

    def top(self, question: list[str], k: int) -> list[int]:
        """The rows of the k passages with the highest scores, a tie going to the earlier
        passage."""
        return np.argsort(-self.scores(question), kind="stable")[:k].tolist()
