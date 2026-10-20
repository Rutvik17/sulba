"""The help desk's passages searched with Postgres's full-text search: each passage's words
kept beside it as a tsvector, and the passages found that hold every word of a question, or
any."""

from collections.abc import Iterable

import psycopg

EVERY = (
    "SELECT id FROM passages, websearch_to_tsquery('english', %(question)s) AS query "
    "WHERE words @@ query ORDER BY ts_rank_cd(words, query) DESC, id LIMIT %(k)s"
)
# plainto_tsquery joins the question's words with &, and each & made | joins them with OR.
ANY = (
    "WITH asked AS (SELECT replace(plainto_tsquery('english', %(question)s)::text, "
    "'&', '|')::tsquery AS query) "
    "SELECT id FROM passages, asked "
    "WHERE words @@ query ORDER BY ts_rank_cd(words, query) DESC, id LIMIT %(k)s"
)


def load(conn: psycopg.Connection, rows: Iterable[tuple[str, str]]) -> None:
    """The passages table, each row a passage's id and text."""
    conn.execute("CREATE TABLE passages (id text PRIMARY KEY, body text NOT NULL)")
    with (
        conn.cursor() as cursor,
        cursor.copy("COPY passages (id, body) FROM STDIN") as copy,
    ):
        for row in rows:
            copy.write_row(row)
    conn.execute("ANALYZE passages")


def index(conn: psycopg.Connection) -> None:
    """Each passage's words, as Postgres's English configuration finds them in its body,
    kept in the column words, and a GIN index on them."""
    conn.execute(
        "ALTER TABLE passages ADD COLUMN words tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', body)) STORED"
    )
    conn.execute("CREATE INDEX passages_words ON passages USING gin (words)")


def every_word(conn: psycopg.Connection, question: str, k: int = 5) -> list[str]:
    """The ids of the k passages that hold every word of the question, best first by
    ts_rank_cd, a tie going to the id that sorts first."""
    rows = conn.execute(EVERY, {"question": question, "k": k}).fetchall()
    return [id_ for (id_,) in rows]


def any_word(conn: psycopg.Connection, question: str, k: int = 5) -> list[str]:
    """The ids of the k passages that hold any word of the question, best first by
    ts_rank_cd, a tie going to the id that sorts first."""
    rows = conn.execute(ANY, {"question": question, "k": k}).fetchall()
    return [id_ for (id_,) in rows]
