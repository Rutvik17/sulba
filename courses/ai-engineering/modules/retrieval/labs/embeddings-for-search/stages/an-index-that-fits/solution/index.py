"""The help desk's index: each passage's vector kept in a few bytes, and searched for
each question."""

from pathlib import Path

import httpx
import numpy as np

from cache import Cache
from embed import DOCUMENT, QUERY
from shorten import bounds, quantize, restore, shorten

# How many numbers of each vector the index keeps, a byte each.
NUMBERS = 256


class Index:
    """The passages' ids, and their vectors as codes of a byte for each number."""

    def __init__(
        self, ids: list[str], codes: np.ndarray, low: np.ndarray, high: np.ndarray
    ):
        self.ids = ids
        self.codes = codes
        self.low = low
        self.high = high
        self.vectors = restore(codes, low, high)

    @classmethod
    def build(
        cls, client: httpx.Client, cache: Cache, passages: dict[str, str]
    ) -> "Index":
        """The index of the passages, by id, each embedded through the cache."""
        vectors = shorten(
            cache.vectors(client, list(passages.values()), DOCUMENT), NUMBERS
        )
        low, high = bounds(vectors)
        return cls(list(passages), quantize(vectors, low, high), low, high)

    def find(
        self, client: httpx.Client, cache: Cache, questions: list[str], k: int = 5
    ) -> list[list[str]]:
        """The ids of each question's k best passages, best first."""
        asked = shorten(cache.vectors(client, questions, QUERY), NUMBERS)
        scores = asked @ self.vectors.T
        best = np.argsort(-scores, axis=1, kind="stable")[:, :k]
        return [[self.ids[index] for index in row] for row in best]

    def save(self, path: Path) -> None:
        """The index, in one file."""
        with open(path, "wb") as file:
            np.savez(
                file,
                ids=np.array(self.ids),
                codes=self.codes,
                low=self.low,
                high=self.high,
            )

    @classmethod
    def load(cls, path: Path) -> "Index":
        """The index save wrote."""
        with np.load(path) as saved:
            return cls(
                saved["ids"].tolist(), saved["codes"], saved["low"], saved["high"]
            )
