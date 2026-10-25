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

SESSION_MIGRATIONS: list[Migration] = []


@dataclass(frozen=True)
class Account:
    """A person who has signed in: their id in the database, and their email and name."""

    id: int
    email: str | None
    name: str | None


def hashed(token: str) -> str:
    """The token's SHA-256, in hex, which the database keeps in its place."""
    raise NotImplementedError


class Sessions:
    """Sign-ins and sessions, in the database the pool connects to, whose connections are in
    autocommit mode."""

    def __init__(self, pool: ConnectionPool) -> None:
        self.pool = pool

    def begin(self, pending: Pending, back: str) -> str:
        """Keeps a sign-in on its way, and the path to send the person back to once it's done,
        and gives the token for the browser's sign-in cookie."""
        raise NotImplementedError

    def take(self, token: str) -> tuple[Pending, str] | None:
        """The sign-in the token was given for, and its path back, once: it's gone after. None
        when there's no such sign-in, or it started too long ago."""
        raise NotImplementedError

    def open(self, person: Person) -> str:
        """A new session for the person, who is kept, or brought up to date, under their issuer
        and subject, and the token for the browser's session cookie."""
        raise NotImplementedError

    def find(self, token: str) -> Account | None:
        """The account of the session the token was given for, or None when there's no such
        session or it has ended."""
        raise NotImplementedError

    def close(self, token: str) -> None:
        """Ends the session the token was given for, if there is one."""
        raise NotImplementedError


def signed_in(request: Request) -> Account:
    """The account of the request's session, or a 403: a request without a session, or with
    one that has ended, is refused."""
    raise NotImplementedError
