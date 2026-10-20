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
    conn.execute(
        sql.SQL(
            "CREATE INDEX {} ON passages USING hnsw (embedding vector_cosine_ops) "
            "WITH (m = {}, ef_construction = {})"
        ).format(sql.Identifier(INDEX), sql.Literal(m), sql.Literal(ef_construction))
    )


def search(
    conn: psycopg.Connection, vector: np.ndarray, k: int = 10, ef_search: int = 40
) -> list[str]:
    """The ids of the k passages nearest to vector, nearest first, through the index
    with a list of ef_search candidates, for this search alone."""
    with conn.transaction():
        conn.execute("SELECT set_config('hnsw.ef_search', %s, true)", (str(ef_search),))
        rows = conn.execute(
            "SELECT id FROM passages ORDER BY embedding <=> %s LIMIT %s", (vector, k)
        ).fetchall()
    return [id_ for (id_,) in rows]


def uses_index(conn: psycopg.Connection, vector: np.ndarray, k: int = 10) -> bool:
    """Whether Postgres's plan finds the k passages nearest to vector through the
    index."""
    plan = conn.execute(
        "EXPLAIN (FORMAT JSON) SELECT id FROM passages ORDER BY embedding <=> %s LIMIT %s",
        (vector, k),
    ).fetchone()[0]
    return INDEX in names(plan[0]["Plan"])


def names(node: dict[str, Any]) -> set[str]:
    """The indexes a plan's node and the nodes under it scan."""
    found = {node["Index Name"]} if "Index Name" in node else set()
    for child in node.get("Plans", []):
        found |= names(child)
    return found
