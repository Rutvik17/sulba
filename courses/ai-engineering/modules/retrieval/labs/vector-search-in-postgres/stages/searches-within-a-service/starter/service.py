"""The help desk's searches within one service, through the approximate index."""

import numpy as np
import psycopg


def search_in(
    conn: psycopg.Connection,
    vector: np.ndarray,
    domain: str,
    k: int = 10,
    ef_search: int = 40,
) -> list[str]:
    """The ids of the k passages of domain nearest to vector, nearest first, through the
    index, which goes on scanning until it has k, for this search alone."""
    raise NotImplementedError


def by_service(
    conn: psycopg.Connection, vector: np.ndarray, k: int = 5
) -> dict[str, list[str]]:
    """The ids of the k passages nearest to vector in each service, by its name."""
    raise NotImplementedError
