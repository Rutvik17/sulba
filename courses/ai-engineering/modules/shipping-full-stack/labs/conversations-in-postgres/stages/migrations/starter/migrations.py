"""The desk's schema, as migrations: each one applied once, in order, in a transaction of its
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


MIGRATIONS = [
    Migration(
        1,
        "conversations",
        """
        CREATE TABLE conversations (
            id text PRIMARY KEY,
            page text CHECK (page IN ('ssa', 'va', 'studentaid', 'dmv')),
            started_at timestamptz NOT NULL DEFAULT now()
        )
        """,
    ),
]

# The key every copy of the app takes Postgres's advisory lock on while it migrates.
LOCK = 2_041_873


class MigrationError(Exception):
    """The migrations can't be applied as they are."""


def migrate(
    conn: psycopg.Connection, migrations: list[Migration] = MIGRATIONS
) -> list[int]:
    """Applies each migration not yet applied, in order, each in its own transaction, and gives
    the versions it applied. conn is in autocommit mode. Two apps that migrate at once take turns:
    the second applies nothing the first has."""
    raise NotImplementedError
