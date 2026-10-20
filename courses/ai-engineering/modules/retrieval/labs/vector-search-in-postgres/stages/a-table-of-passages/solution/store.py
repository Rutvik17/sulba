"""The help desk's passages in Postgres, each with its vector, searched exactly."""

from collections.abc import Iterable

import numpy as np
import psycopg
from pgvector.psycopg import register_vector


def connect(url: str) -> psycopg.Connection:
    """A connection to the database at url, in autocommit mode, that sends NumPy arrays
    as vectors."""
    conn = psycopg.connect(url, autocommit=True)
    register_vector(conn)
    return conn


def create(conn: psycopg.Connection) -> None:
    """The passages table: each passage's id, service, page, text and vector, the vector
    kept in its row."""
    conn.execute(
        "CREATE TABLE passages ("
        "id text PRIMARY KEY, "
        "domain text NOT NULL, "
        "page text NOT NULL, "
        "body text NOT NULL, "
        "embedding vector(768) STORAGE PLAIN NOT NULL)"
    )


def load(
    conn: psycopg.Connection, rows: Iterable[tuple[str, str, str, str, np.ndarray]]
) -> None:
    """The rows, each a passage's id, domain, page, body and vector, into the table with
    one COPY in its binary format, then the planner's statistics on them."""
    statement = "COPY passages (id, domain, page, body, embedding) FROM STDIN WITH (FORMAT BINARY)"
    with conn.cursor() as cursor, cursor.copy(statement) as copy:
        copy.set_types(["text", "text", "text", "text", "vector"])
        for row in rows:
            copy.write_row(row)
    conn.execute("ANALYZE passages")


def nearest(conn: psycopg.Connection, vector: np.ndarray, k: int = 10) -> list[str]:
    """The ids of the k passages nearest to vector by cosine distance, nearest first."""
    rows = conn.execute(
        "SELECT id FROM passages ORDER BY embedding <=> %s LIMIT %s", (vector, k)
    ).fetchall()
    return [id_ for (id_,) in rows]
