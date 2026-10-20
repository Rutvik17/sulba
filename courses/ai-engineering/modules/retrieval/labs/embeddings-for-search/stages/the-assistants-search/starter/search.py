"""The help desk's search, as the assistant wrote it: each passage's vector cut to
NUMBERS numbers of a byte each, and each question's best passages first."""

import httpx
import numpy as np

from cache import Cache
from embed import DOCUMENT, QUERY
from shorten import bounds, quantize, restore, shorten

NUMBERS = 256


def cut(vectors: np.ndarray) -> np.ndarray:
    """Each vector cut to NUMBERS numbers."""
    return vectors[:, :NUMBERS]


class Search:
    """The help desk's passages, by id, searched by their vectors."""

    def __init__(
        self, client: httpx.Client, cache: Cache, passages: dict[str, str]
    ) -> None:
        self.client = client
        self.cache = cache
        self.ids = sorted(passages)
        vectors = cut(cache.vectors(client, list(passages.values()), DOCUMENT))
        self.low, self.high = bounds(vectors)
        self.codes = quantize(vectors, self.low, self.high)

    def find(self, questions: list[str], k: int = 5) -> list[list[str]]:
        """The ids of each question's k best passages, best first."""
        asked = cut(self.cache.vectors(self.client, questions, DOCUMENT))
        scores = asked @ restore(self.codes, self.low, self.high).T
        best = np.argsort(scores, axis=1)[:, -k:]
        return [[self.ids[index] for index in row] for row in best]
