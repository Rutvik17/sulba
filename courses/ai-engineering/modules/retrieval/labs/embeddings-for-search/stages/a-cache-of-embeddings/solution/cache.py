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
    return hashlib.sha256(f"{MODEL}\n{prefix}{text}".encode()).hexdigest()


class Cache:
    """Vectors kept by their texts' keys in an SQLite file."""

    def __init__(self, path: Path) -> None:
        self.connection = sqlite3.connect(path)
        with self.connection:
            self.connection.execute(
                "CREATE TABLE IF NOT EXISTS vectors"
                " (key TEXT PRIMARY KEY, vector BLOB NOT NULL)"
            )

    def vectors(
        self, client: httpx.Client, texts: list[str], prefix: str, batch: int = BATCH
    ) -> np.ndarray:
        """Each text's vector, embedded after prefix, as the rows of a float32 array in
        the texts' order. Texts the file has no vector for are embedded once each, in
        batches of at most batch, and each batch is kept as it comes."""
        keys = [key(prefix, text) for text in texts]
        found = self.kept(keys)
        missing = list(
            dict.fromkeys(text for text, k in zip(texts, keys) if k not in found)
        )
        for start in range(0, len(missing), batch):
            part = missing[start : start + batch]
            vectors = embed(client, part, prefix, batch)
            rows = [(key(prefix, text), vector) for text, vector in zip(part, vectors)]
            with self.connection:
                self.connection.executemany(
                    "INSERT INTO vectors (key, vector) VALUES (?, ?)",
                    [(k, vector.tobytes()) for k, vector in rows],
                )
            found.update(rows)
        if not keys:
            return np.zeros((0, 0), dtype=np.float32)
        return np.array([found[k] for k in keys], dtype=np.float32)

    def kept(self, keys: list[str]) -> dict[str, np.ndarray]:
        """The vectors the file has for these keys, asked for 500 at a time."""
        found: dict[str, np.ndarray] = {}
        distinct = list(dict.fromkeys(keys))
        for start in range(0, len(distinct), 500):
            part = distinct[start : start + 500]
            marks = ", ".join("?" * len(part))
            query = f"SELECT key, vector FROM vectors WHERE key IN ({marks})"
            for k, blob in self.connection.execute(query, part):
                found[k] = np.frombuffer(blob, dtype=np.float32)
        return found

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "Cache":
        return self

    def __exit__(self, *exception: object) -> None:
        self.close()
