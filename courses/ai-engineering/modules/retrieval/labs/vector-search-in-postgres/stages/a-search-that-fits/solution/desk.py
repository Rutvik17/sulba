"""The help desk's search as it ships: an index of each passage's first 256 numbers at
half precision, whose candidates are sorted by the full vectors."""

from collections.abc import Iterable

import numpy as np
import psycopg

INDEX = (
    "CREATE INDEX passages_short ON passages USING hnsw "
    "((subvector(embedding, 1, 256)::halfvec(256)) halfvec_cosine_ops)"
)
# The index's 40 nearest candidates, by the same expression it's built on, then the k
# nearest of them by the full vectors.
EVERY = (
    "SELECT id FROM (SELECT id, embedding FROM passages "
    "ORDER BY subvector(embedding, 1, 256)::halfvec(256) "
    "<=> subvector(%(vector)s::vector, 1, 256)::halfvec(256) LIMIT 40) AS candidates "
    "ORDER BY embedding <=> %(vector)s LIMIT %(k)s"
)
WITHIN = (
    "SELECT id FROM (SELECT id, embedding FROM passages WHERE domain = %(domain)s "
    "ORDER BY subvector(embedding, 1, 256)::halfvec(256) "
    "<=> subvector(%(vector)s::vector, 1, 256)::halfvec(256) LIMIT 40) AS candidates "
    "ORDER BY embedding <=> %(vector)s LIMIT %(k)s"
)


def build(conn: psycopg.Connection) -> None:
    """The index the search goes through, on the loaded passages."""
    conn.execute(INDEX)


def search(
    conn: psycopg.Connection,
    vector: np.ndarray,
    k: int = 10,
    domain: str | None = None,
) -> list[str]:
    """The ids of the k passages nearest to vector by the full vectors' cosine distance,
    nearest first, through an index, and only the service domain's if it's given."""
    with conn.transaction():
        conn.execute("SELECT set_config('hnsw.iterative_scan', 'relaxed_order', true)")
        rows = conn.execute(
            EVERY if domain is None else WITHIN,
            {"vector": vector, "domain": domain, "k": k},
        ).fetchall()
    return [id_ for (id_,) in rows]


def update(
    conn: psycopg.Connection, rows: Iterable[tuple[str, str, str, str, np.ndarray]]
) -> None:
    """Each row, a passage's id, domain, page, body and vector, into the table: added,
    or in place of the passage with its id."""
    with conn.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO passages (id, domain, page, body, embedding) "
            "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET "
            "domain = EXCLUDED.domain, page = EXCLUDED.page, body = EXCLUDED.body, "
            "embedding = EXCLUDED.embedding",
            list(rows),
        )
