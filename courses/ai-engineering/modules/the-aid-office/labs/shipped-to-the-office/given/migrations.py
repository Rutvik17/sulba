"""The desk's own tables, as migrations: each one applied once, in order, in a transaction of its
own, and recorded with a checksum of its SQL, so a migration changed after it ran is caught."""

import hashlib
from dataclasses import dataclass

import psycopg


@dataclass(frozen=True)
class Migration:
    """A change to the schema: its version, its name and its SQL."""

    version: int
    name: str
    sql: str

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.sql.encode()).hexdigest()


# The key every copy of the app takes Postgres's advisory lock on while it migrates.
LOCK = 2_041_873


class MigrationError(Exception):
    """The migrations can't be applied as they are."""


def migrate(conn: psycopg.Connection, migrations: list[Migration]) -> list[int]:
    """Applies each migration not yet applied, in order, each in its own transaction, and gives
    the versions it applied. conn is in autocommit mode. Two apps that migrate at once take turns:
    the second applies nothing the first has."""
    if [each.version for each in migrations] != list(range(1, len(migrations) + 1)):
        raise MigrationError("The migrations' versions go 1, 2, 3 and so on, in order.")
    conn.execute("SELECT pg_advisory_lock(%s)", [LOCK])
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version integer PRIMARY KEY,
                name text NOT NULL,
                checksum text NOT NULL,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        applied = dict(
            conn.execute("SELECT version, checksum FROM schema_migrations").fetchall()
        )
        for each in migrations:
            if each.version in applied:
                if applied[each.version] != each.checksum:
                    raise MigrationError(
                        f"Migration {each.version}, {each.name}, has changed since it was "
                        "applied: add a new migration instead."
                    )
                continue
            with conn.transaction():
                conn.execute(each.sql)
                conn.execute(
                    "INSERT INTO schema_migrations (version, name, checksum) "
                    "VALUES (%s, %s, %s)",
                    [each.version, each.name, each.checksum],
                )
        return [each.version for each in migrations if each.version not in applied]
    finally:
        conn.execute("SELECT pg_advisory_unlock(%s)", [LOCK])
