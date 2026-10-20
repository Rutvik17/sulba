"""The help desk's store of the vectors it has embedded, so that it embeds each text
once."""

import hashlib
import sqlite3
from pathlib import Path

import httpx
import numpy as np

from embed import BATCH, MODEL, embed


def key(prefix: str, text: str) -> str:
    """The text's key: the sha256 of the model's name, a newline, the prefix and the
    text."""
    raise NotImplementedError


class Cache:
    """Vectors kept by their texts' keys in an SQLite file."""

    def __init__(self, path: Path) -> None:
        raise NotImplementedError

    def vectors(
        self, client: httpx.Client, texts: list[str], prefix: str, batch: int = BATCH
    ) -> np.ndarray:
        """Each text's vector, embedded after prefix, as the rows of a float32 array in
        the texts' order. Texts the file has no vector for are embedded once each, in
        batches of at most batch, and each batch is kept as it comes."""
        raise NotImplementedError

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "Cache":
        return self

    def __exit__(self, *exception: object) -> None:
        self.close()
