"""Who's signed in: each sign-in on its way, the people the provider has signed in, and their
sessions, kept in Postgres. A browser holds only random tokens, and the database only their
hashes, so a copy of the database signs no one in."""

import hashlib
import secrets
from dataclasses import dataclass

from fastapi import Request
from psycopg_pool import ConnectionPool
from starlette.exceptions import HTTPException

from migrations import Migration
from sign_in import Pending
from tokens import Person

# A sign-in is finished within this many minutes of its start, or started again.
SIGN_IN_MINUTES = 10
# A session lasts this many days from the sign-in that opened it, however much it's used.
SESSION_DAYS = 7
# The cookies that carry a sign-in on its way and a session.
SIGN_IN_COOKIE = "desk_sign_in"
SESSION_COOKIE = "desk_session"

SESSION_MIGRATIONS = [
    Migration(
        4,
        "people",
        """
        CREATE TABLE people (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            issuer text NOT NULL,
            subject text NOT NULL,
            email text,
            name text,
            UNIQUE (issuer, subject)
        )
        """,
    ),
    Migration(
        5,
        "sign_ins",
        """
        CREATE TABLE sign_ins (
            id text PRIMARY KEY,
            state text NOT NULL,
            nonce text NOT NULL,
            verifier text NOT NULL,
            back text NOT NULL,
            started_at timestamptz NOT NULL DEFAULT now()
        )
        """,
    ),
    Migration(
        6,
        "sessions",
        """
        CREATE TABLE sessions (
            id text PRIMARY KEY,
            person_id bigint NOT NULL REFERENCES people ON DELETE CASCADE,
            started_at timestamptz NOT NULL DEFAULT now(),
            expires_at timestamptz NOT NULL
        )
        """,
    ),
]


@dataclass(frozen=True)
class Account:
    """A person who has signed in: their id in the database, and their email and name."""

    id: int
    email: str | None
    name: str | None


def hashed(token: str) -> str:
    """The token's SHA-256, in hex, which the database keeps in its place."""
    return hashlib.sha256(token.encode()).hexdigest()


class Sessions:
    """Sign-ins and sessions, in the database the pool connects to, whose connections are in
    autocommit mode."""

    def __init__(self, pool: ConnectionPool) -> None:
        self.pool = pool

    def begin(self, pending: Pending, back: str) -> str:
        """Keeps a sign-in on its way, and the path to send the person back to once it's done,
        and gives the token for the browser's sign-in cookie."""
        token = secrets.token_urlsafe(32)
        with self.pool.connection() as conn:
            conn.execute(
                "INSERT INTO sign_ins (id, state, nonce, verifier, back) "
                "VALUES (%s, %s, %s, %s, %s)",
                [hashed(token), pending.state, pending.nonce, pending.verifier, back],
            )
        return token

    def take(self, token: str) -> tuple[Pending, str] | None:
        """The sign-in the token was given for, and its path back, once: it's gone after. None
        when there's no such sign-in, or it started too long ago."""
        with self.pool.connection() as conn:
            found = conn.execute(
                "DELETE FROM sign_ins WHERE id = %s RETURNING state, nonce, verifier, back, "
                "started_at > now() - make_interval(mins => %s)",
                [hashed(token), SIGN_IN_MINUTES],
            ).fetchone()
        if found is None or not found[4]:
            return None
        state, nonce, verifier, back, _ = found
        return Pending(state, nonce, verifier), back

    def open(self, person: Person) -> str:
        """A new session for the person, who is kept, or brought up to date, under their issuer
        and subject, and the token for the browser's session cookie."""
        token = secrets.token_urlsafe(32)
        with self.pool.connection() as conn, conn.transaction():
            (person_id,) = conn.execute(
                "INSERT INTO people (issuer, subject, email, name) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (issuer, subject) "
                "DO UPDATE SET email = EXCLUDED.email, name = EXCLUDED.name RETURNING id",
                [person.issuer, person.subject, person.email, person.name],
            ).fetchone()
            conn.execute(
                "INSERT INTO sessions (id, person_id, expires_at) "
                "VALUES (%s, %s, now() + make_interval(days => %s))",
                [hashed(token), person_id, SESSION_DAYS],
            )
        return token

    def find(self, token: str) -> Account | None:
        """The account of the session the token was given for, or None when there's no such
        session or it has ended."""
        with self.pool.connection() as conn:
            found = conn.execute(
                "SELECT people.id, people.email, people.name FROM sessions "
                "JOIN people ON people.id = sessions.person_id "
                "WHERE sessions.id = %s AND sessions.expires_at > now()",
                [hashed(token)],
            ).fetchone()
        return None if found is None else Account(*found)

    def close(self, token: str) -> None:
        """Ends the session the token was given for, if there is one."""
        with self.pool.connection() as conn:
            conn.execute("DELETE FROM sessions WHERE id = %s", [hashed(token)])


def signed_in(request: Request) -> Account:
    """The account of the request's session, or a 403: a request without a session, or with
    one that has ended, is refused."""
    sessions: Sessions = request.app.state.sessions
    token = request.cookies.get(SESSION_COOKIE)
    account = sessions.find(token) if token else None
    if account is None:
        raise HTTPException(403, "Sign in first.")
    return account
