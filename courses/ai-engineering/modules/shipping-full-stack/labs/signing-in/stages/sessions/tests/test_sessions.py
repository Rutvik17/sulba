import hashlib
from datetime import timedelta

import psycopg
import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from psycopg_pool import ConnectionPool

from conversations import install
from migrations import MIGRATIONS, migrate
from sessions import (
    SESSION_COOKIE,
    SESSION_MIGRATIONS,
    Account,
    Sessions,
    signed_in,
)
from sign_in import Pending
from tokens import Person

ADA = Person("https://id.test", "user-ada", "ada@example.com", "Ada")
GRACE = Person("https://id.test", "user-grace", "grace@example.com", "Grace")


@pytest.fixture
def pool(database):
    with psycopg.connect(database, autocommit=True) as conn:
        migrate(conn, [*MIGRATIONS, *SESSION_MIGRATIONS])
    with ConnectionPool(database, kwargs={"autocommit": True}) as pool:
        yield pool


def cookie(token):
    return {"Cookie": f"{SESSION_COOKIE}={token}"}


def rows(pool, sql, params=()):
    with pool.connection() as conn:
        return conn.execute(sql, params).fetchall()


def run(pool, sql, params=()):
    with pool.connection() as conn:
        conn.execute(sql, params)


@pytest.mark.id("tst_0ujg3l")
def test_the_tables_come_after_the_conversations(database):
    """The migrations come after the desk's own, as versions 4, 5 and 6"""
    with psycopg.connect(database, autocommit=True) as conn:
        assert migrate(conn, [*MIGRATIONS, *SESSION_MIGRATIONS]) == [1, 2, 3, 4, 5, 6]
        tables = conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY 1"
        ).fetchall()
    assert [name for (name,) in tables] == [
        "conversations",
        "messages",
        "people",
        "schema_migrations",
        "sessions",
        "sign_ins",
        "turns",
    ]


@pytest.mark.id("tst_zy0rq2")
def test_a_sign_in_is_taken_once(pool):
    """A sign-in comes back once, with its path back, and then it's gone"""
    sessions = Sessions(pool)
    pending = Pending.new()
    token = sessions.begin(pending, "/conversations")
    assert sessions.take(token) == (pending, "/conversations")
    assert sessions.take(token) is None
    assert sessions.take(Pending.new().state) is None


@pytest.mark.id("tst_1vjfnw")
def test_an_old_sign_in_is_refused(pool):
    """A sign-in started more than 10 minutes ago doesn't come back"""
    sessions = Sessions(pool)
    fresh, old = Pending.new(), Pending.new()
    fresh_token = sessions.begin(fresh, "/")
    old_token = sessions.begin(old, "/")
    run(
        pool,
        "UPDATE sign_ins SET started_at = now() - interval '9 minutes' WHERE state = %s",
        [fresh.state],
    )
    run(
        pool,
        "UPDATE sign_ins SET started_at = now() - interval '11 minutes' WHERE state = %s",
        [old.state],
    )
    assert sessions.take(fresh_token) == (fresh, "/")
    assert sessions.take(old_token) is None


@pytest.mark.id("tst_t04i4a")
def test_the_database_holds_hashes_of_tokens(pool):
    """The database keeps each token's SHA-256 in hex, never the token"""
    sessions = Sessions(pool)
    sign_in = sessions.begin(Pending.new(), "/")
    session = sessions.open(ADA)
    for token in (sign_in, session):
        assert len(token) >= 43
    ids = {
        id
        for (id,) in rows(pool, "SELECT id FROM sign_ins UNION SELECT id FROM sessions")
    }
    assert ids == {
        hashlib.sha256(sign_in.encode()).hexdigest(),
        hashlib.sha256(session.encode()).hexdigest(),
    }


@pytest.mark.id("tst_ajri38")
def test_a_session_finds_its_account(pool):
    """A session's token finds its person's account, and another token finds none"""
    sessions = Sessions(pool)
    token = sessions.open(GRACE)
    account = sessions.find(token)
    assert account is not None
    assert (account.email, account.name) == ("grace@example.com", "Grace")
    assert sessions.find(Pending.new().state) is None


@pytest.mark.id("tst_3iqhop")
def test_each_sign_in_opens_a_new_session(pool):
    """Each sign-in gives a new token, for the same account"""
    sessions = Sessions(pool)
    first, second = sessions.open(ADA), sessions.open(ADA)
    assert first != second
    assert sessions.find(first) == sessions.find(second)


@pytest.mark.id("tst_kcy5qc")
def test_a_person_is_their_issuer_and_subject(pool):
    """The same issuer and subject find the same account, with their email brought up to
    date, and anyone else, even with the same email, another"""
    sessions = Sessions(pool)
    ada = sessions.find(sessions.open(ADA))
    moved = Person("https://id.test", "user-ada", "ada@moved.example", "Ada")
    again = sessions.find(sessions.open(moved))
    same_email = Person("https://id.test", "user-mallory", "ada@example.com", "Mallory")
    other_issuer = Person(
        "https://elsewhere.test", "user-ada", "ada@example.com", "Ada"
    )
    assert again == Account(ada.id, "ada@moved.example", "Ada")
    others = {
        sessions.find(sessions.open(each)).id for each in (same_email, other_issuer)
    }
    assert len(others) == 2
    assert ada.id not in others


@pytest.mark.id("tst_34o7vt")
def test_a_session_lasts_seven_days(pool):
    """A session ends seven days after it opens, however much it's used"""
    sessions = Sessions(pool)
    token = sessions.open(ADA)
    [(lasts,)] = rows(pool, "SELECT expires_at - started_at FROM sessions")
    assert lasts == timedelta(days=7)
    run(pool, "UPDATE sessions SET expires_at = now() - interval '1 second'")
    assert sessions.find(token) is None


@pytest.mark.id("tst_i7yro4")
def test_a_closed_session_finds_no_one(pool):
    """A closed session finds no account, and the person's other sessions carry on"""
    sessions = Sessions(pool)
    phone, laptop = sessions.open(ADA), sessions.open(ADA)
    sessions.close(phone)
    assert sessions.find(phone) is None
    assert sessions.find(laptop) is not None


@pytest.mark.id("tst_2hujoh")
def test_a_route_for_people_signed_in(loop, pool):
    """A route that depends on signed_in gets the account of the request's session, and
    a request without one, or with one that has ended, is refused with 403"""
    sessions = Sessions(pool)
    app = FastAPI()
    install(app)
    app.state.sessions = sessions

    @app.get("/me")
    def me(person: Account = Depends(signed_in)) -> Account:
        return person

    token, ended = sessions.open(ADA), sessions.open(ADA)
    sessions.close(ended)

    async def go():
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="https://desk.test"
        ) as client:
            found = await client.get("/me", headers=cookie(token))
            refused = [
                await client.get("/me", headers=headers)
                for headers in ({}, cookie(ended), cookie("a-guess"))
            ]
        return found, refused

    found, refused = loop.run_until_complete(go())
    assert found.status_code == 200
    assert found.json()["email"] == "ada@example.com"
    assert [each.status_code for each in refused] == [403, 403, 403]
    assert refused[0].headers["content-type"] == "application/problem+json"
