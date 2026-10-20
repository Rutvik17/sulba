"""The help desk's passages in Postgres, each with its vector, searched exactly."""

from collections.abc import Iterable

import numpy as np
import psycopg
from pgvector.psycopg import register_vector


def connect(url: str) -> psycopg.Connection:
    """A connection to the database at url, in autocommit mode, that sends NumPy arrays
    as vectors."""
    raise NotImplementedError


def create(conn: psycopg.Connection) -> None:
    """The passages table: each passage's id, service, page, text and vector, the vector
    kept in its row."""
    raise NotImplementedError


def load(
    conn: psycopg.Connection, rows: Iterable[tuple[str, str, str, str, np.ndarray]]
) -> None:
    """The rows, each a passage's id, domain, page, body and vector, into the table with
    one COPY in its binary format, then the planner's statistics on them."""
    raise NotImplementedError


def nearest(conn: psycopg.Connection, vector: np.ndarray, k: int = 10) -> list[str]:
    """The ids of the k passages nearest to vector by cosine distance, nearest first."""
    raise NotImplementedError
