"""The help desk's search page: its queries on the passages, through their index."""

import numpy as np
import psycopg

# Iterative index scans in relaxed order, for a search within a service.
RELAXED = "SELECT set_config('hnsw.iterative_scan', 'relaxed_order', true)"


def search(
    conn: psycopg.Connection, vector: np.ndarray, k: int = 10
) -> list[tuple[str, float]]:
    """The k passages nearest to vector, nearest first: each its id and its cosine
    similarity, 1 less its cosine distance."""
    return conn.execute(
        "SELECT id, 1 - (embedding <=> %s) AS similarity FROM passages "
        "ORDER BY embedding <=> %s LIMIT %s",
        (vector, vector, k),
    ).fetchall()


def search_in(
    conn: psycopg.Connection, vector: np.ndarray, domain: str, k: int = 10
) -> list[str]:
    """The ids of the k passages of the service domain nearest to vector, nearest
    first."""
    query = (
        "WITH found AS MATERIALIZED ("
        "SELECT id, embedding <=> %(vector)s AS distance FROM passages "
        "WHERE domain = %(domain)s ORDER BY distance LIMIT %(k)s) "
        "SELECT id FROM found ORDER BY distance + 0"
    )
    with conn.transaction():
        conn.execute(RELAXED)
        rows = conn.execute(query, {"vector": vector, "domain": domain, "k": k})
        return [id_ for (id_,) in rows]


def similar(conn: psycopg.Connection, passage: str, k: int = 5) -> list[str]:
    """The ids of the k passages most like the passage with the id passage, most alike
    first, without it."""
    rows = conn.execute(
        "SELECT id FROM passages WHERE id <> %(id)s ORDER BY embedding "
        "<=> (SELECT embedding FROM passages WHERE id = %(id)s) LIMIT %(k)s",
        {"id": passage, "k": k},
    )
    return [id_ for (id_,) in rows]
