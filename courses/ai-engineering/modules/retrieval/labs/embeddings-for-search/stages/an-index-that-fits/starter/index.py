"""The help desk's index: each passage's vector kept in a few bytes, and searched for
each question."""

from pathlib import Path

import httpx
import numpy as np

from cache import Cache
from embed import DOCUMENT, QUERY
from shorten import bounds, quantize, restore, shorten


class Index:
    """The passages' ids, and their vectors in a few bytes each."""

    @classmethod
    def build(
        cls, client: httpx.Client, cache: Cache, passages: dict[str, str]
    ) -> "Index":
        """The index of the passages, by id, each embedded through the cache."""
        raise NotImplementedError

    def find(
        self, client: httpx.Client, cache: Cache, questions: list[str], k: int = 5
    ) -> list[list[str]]:
        """The ids of each question's k best passages, best first, and of two that tie,
        the one that comes first in the passages."""
        raise NotImplementedError

    def save(self, path: Path) -> None:
        """The index, in one file."""
        raise NotImplementedError

    @classmethod
    def load(cls, path: Path) -> "Index":
        """The index save wrote."""
        raise NotImplementedError
