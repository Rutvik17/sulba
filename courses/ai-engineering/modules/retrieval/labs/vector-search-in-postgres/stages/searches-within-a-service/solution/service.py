"""The help desk's searches within one service, through the approximate index."""

import numpy as np
import psycopg

# The relaxed scan's rows, found first in the CTE, then sorted: `+ 0` keeps Postgres
# from taking the CTE's ORDER BY as the outer one's.
QUERY = (
    "WITH found AS MATERIALIZED ("
    "SELECT id, embedding <=> %s AS distance FROM passages "
    "WHERE domain = %s ORDER BY distance LIMIT %s) "
    "SELECT id FROM found ORDER BY distance + 0"
)


def search_in(
    conn: psycopg.Connection,
    vector: np.ndarray,
    domain: str,
    k: int = 10,
    ef_search: int = 40,
) -> list[str]:
    """The ids of the k passages of domain nearest to vector, nearest first, through the
    index, which goes on scanning until it has k, for this search alone."""
    with conn.transaction():
        conn.execute("SELECT set_config('hnsw.ef_search', %s, true)", (str(ef_search),))
        conn.execute("SELECT set_config('hnsw.iterative_scan', 'relaxed_order', true)")
        rows = conn.execute(QUERY, (vector, domain, k)).fetchall()
    return [id_ for (id_,) in rows]


def by_service(
    conn: psycopg.Connection, vector: np.ndarray, k: int = 5
) -> dict[str, list[str]]:
    """The ids of the k passages nearest to vector in each service, by its name."""
    rows = conn.execute(
        "SELECT DISTINCT domain FROM passages ORDER BY domain"
    ).fetchall()
    return {domain: search_in(conn, vector, domain, k) for (domain,) in rows}
