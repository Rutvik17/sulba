"""The help desk's search as it ships."""

from collections.abc import Iterable

import numpy as np
import psycopg


def build(conn: psycopg.Connection) -> None:
    """The indexes the search goes through, on the loaded passages."""
    raise NotImplementedError


def search(
    conn: psycopg.Connection,
    vector: np.ndarray,
    k: int = 10,
    domain: str | None = None,
) -> list[str]:
    """The ids of the k passages nearest to vector by the full vectors' cosine distance,
    nearest first, through an index, and only the service domain's if it's given."""
    raise NotImplementedError


def update(
    conn: psycopg.Connection, rows: Iterable[tuple[str, str, str, str, np.ndarray]]
) -> None:
    """Each row, a passage's id, domain, page, body and vector, into the table: added,
    or in place of the passage with its id."""
    raise NotImplementedError
