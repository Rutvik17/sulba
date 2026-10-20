"""The help desk's passages searched through an approximate index, HNSW."""

from typing import Any

import numpy as np
import psycopg
from psycopg import sql

# The index's name, which the plan names when a search goes through it.
INDEX = "passages_embedding"


def build(conn: psycopg.Connection, m: int = 16, ef_construction: int = 64) -> None:
    """An HNSW index on the passages' vectors for cosine distance: m links for each
    vector in each layer, and a list of ef_construction candidates as it's built."""
    raise NotImplementedError


def search(
    conn: psycopg.Connection, vector: np.ndarray, k: int = 10, ef_search: int = 40
) -> list[str]:
    """The ids of the k passages nearest to vector, nearest first, through the index
    with a list of ef_search candidates, for this search alone."""
    raise NotImplementedError


def uses_index(conn: psycopg.Connection, vector: np.ndarray, k: int = 10) -> bool:
    """Whether Postgres's plan finds the k passages nearest to vector through the
    index."""
    raise NotImplementedError
