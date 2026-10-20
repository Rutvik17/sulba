"""The help desk's hybrid search: each passage scored by BM25 over its words and by the
cosine of its vector with the question's, and the two put together."""

import math
import re
from collections import Counter

import numpy as np

K1 = 1.5
B = 0.75
WORD = re.compile(r"\w+")
# The vectors' numbers are stored times this.
SCALE = 32767


def words(text: str) -> list[str]:
    """A text's words: its runs of letters, digits and underscores, lowercased."""
    return WORD.findall(text.lower())


def fused(bm25: np.ndarray, similarity: np.ndarray) -> np.ndarray:
    """Each passage's score: its BM25 score and its cosine, added."""
    return bm25 + similarity


class Hybrid:
    """The help desk's passages, by their words and their vectors."""

    def __init__(self, texts: list[str], vectors: np.ndarray) -> None:
        passages = [words(text) for text in texts]
        lengths = np.array([len(passage) for passage in passages], dtype=np.float64)
        self.length = K1 * (1 - B + B * lengths / lengths.mean())
        self.counts = [Counter(passage) for passage in passages]
        held = Counter(word for passage in passages for word in set(passage))
        count = len(passages)
        self.idf = {
            word: math.log((count - n + 0.5) / (n + 0.5)) for word, n in held.items()
        }
        # Each number fits in 16 bits, a quarter of the memory.
        self.vectors = vectors.astype(np.int16)

    def bm25(self, question: str) -> np.ndarray:
        """Each passage's BM25 score for the question."""
        scores = np.zeros(len(self.counts))
        for word in WORD.findall(question):
            if word in self.idf:
                tf = np.array([count[word] for count in self.counts], dtype=np.float64)
                scores += self.idf[word] * tf / (tf + self.length)
        return scores

    def similarity(self, vector: np.ndarray) -> np.ndarray:
        """Each passage's cosine with the question's vector."""
        return (self.vectors @ vector.astype(self.vectors.dtype)) / SCALE**2

    def search(self, question: str, vector: np.ndarray, k: int = 5) -> list[int]:
        """The rows of the k passages that best match the question, best first, a tie
        going to the earlier row."""
        scores = fused(self.bm25(question), self.similarity(vector))
        return np.argsort(-scores, kind="stable")[:k].tolist()
