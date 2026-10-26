"""The office's database, set up for the desk from the office's files: the passages indexed,
the students' records, the directory of their college emails, and the table of questions for
the office's staff. Run it once, and again whenever the office's pages change: what it made the
first time stays, and the passages are brought up to date.

    uv run setup.py
"""

import os
from pathlib import Path

import httpx
from desk import create_tickets
from index import connect, create, read, sync
from office_records import EMAILS
from records import create as create_records
from records import load


def setup(conn, client, data=Path("data")):
    """Makes the office's tables in the database conn is connected to, unless they're there,
    and syncs the passages in data with the model client posts to."""
    if conn.execute("SELECT to_regclass('passages')").fetchone()[0] is None:
        with conn.transaction():
            create(conn)
            create_records(conn)
            load(conn)
            conn.execute(
                "CREATE TABLE directory (email text PRIMARY KEY, "
                "student text NOT NULL REFERENCES students)"
            )
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO directory (student, email) VALUES (%s, %s)", EMAILS
                )
            create_tickets(conn)
    sync(conn, client, read(data / "passages.csv"))


if __name__ == "__main__":
    model_url = os.environ.get("OFFICE_MODEL_URL", "http://127.0.0.1:9931/v1")
    with (
        connect(os.environ["OFFICE_DATABASE_URL"]) as conn,
        httpx.Client(base_url=model_url, timeout=60) as client,
    ):
        setup(conn, client)
