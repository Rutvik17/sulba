from datetime import UTC, datetime

import psycopg
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from psycopg_pool import ConnectionPool

from conversations import Message, install
from conversations import router as conversations_router
from migrations import MIGRATIONS, migrate
from sessions import SESSION_COOKIE, SESSION_MIGRATIONS, Sessions
from store import OWNERS, Store, Usage
from tokens import Person

ADA = Person("https://id.test", "user-ada", "ada@example.com", "Ada")
GRACE = Person("https://id.test", "user-grace", "grace@example.com", "Grace")


@pytest.fixture
def pool(database):
    with psycopg.connect(database, autocommit=True) as conn:
        migrate(conn, [*MIGRATIONS, *SESSION_MIGRATIONS, OWNERS])
    with ConnectionPool(database, kwargs={"autocommit": True}) as pool:
        yield pool


def account(sessions, person):
    """The person's account, and a token for a session of theirs."""
    token = sessions.open(person)
    return sessions.find(token).id, token


def rows(pool, sql, params=()):
    with pool.connection() as conn:
        return conn.execute(sql, params).fetchall()


@pytest.mark.id("tst_xtgxcf")
def test_owners_come_after_the_sessions(database):
    """The owners' migration is version 7, after the sessions' migrations"""
    with psycopg.connect(database, autocommit=True) as conn:
        applied = migrate(conn, [*MIGRATIONS, *SESSION_MIGRATIONS, OWNERS])
        columns = conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'conversations' ORDER BY ordinal_position"
        ).fetchall()
    assert applied == [1, 2, 3, 4, 5, 6, 7]
    assert [name for (name,) in columns] == ["id", "page", "started_at", "owner"]


@pytest.mark.id("tst_8ndmwc")
def test_a_conversation_is_its_owners(pool):
    """A conversation is found by its owner, and by no one else"""
    sessions, store = Sessions(pool), Store(pool)
    (ada, _), (grace, _) = account(sessions, ADA), account(sessions, GRACE)
    started = store.start("dmv", ada)
    assert store.get(started.id, ada) == started
    assert store.get(started.id, grace) is None
    assert store.get("no-such-id", ada) is None


@pytest.mark.id("tst_dtnzda")
def test_each_owner_lists_their_own(pool):
    """Each owner's list has their conversations alone, the newest first, as many as the
    limit"""
    sessions, store = Sessions(pool), Store(pool)
    (ada, _), (grace, _) = account(sessions, ADA), account(sessions, GRACE)
    adas = [store.start(page, ada) for page in ("ssa", "va", None)]
    store.start("dmv", grace)
    for n, conversation in enumerate(adas):
        with pool.connection() as conn:
            conn.execute(
                "UPDATE conversations SET started_at = %s WHERE id = %s",
                [datetime(2026, 10, 1 + n, tzinfo=UTC), conversation.id],
            )
    listed = store.mine(ada)
    assert [each.id for each in listed] == [each.id for each in reversed(adas)]
    assert [each.page for each in listed] == [None, "va", "ssa"]
    assert listed[0].started_at == datetime(2026, 10, 3, tzinfo=UTC)
    assert [each.id for each in store.mine(ada, limit=2)] == [adas[2].id, adas[1].id]
    assert [each.page for each in store.mine(grace)] == ["dmv"]


@pytest.mark.id("tst_i5acs6")
def test_a_conversation_from_before_is_no_ones(pool):
    """A conversation kept before anyone signed in has no owner, and no one finds it"""
    sessions, store = Sessions(pool), Store(pool)
    ada, _ = account(sessions, ADA)
    with pool.connection() as conn:
        conn.execute("INSERT INTO conversations (id, page) VALUES ('before', NULL)")
    assert store.get("before", ada) is None
    assert store.mine(ada) == []


@pytest.mark.id("tst_c953sf")
def test_turns_are_kept_in_the_owners_conversation(pool):
    """A turn kept in an owner's conversation comes back to them in its messages"""
    sessions, store = Sessions(pool), Store(pool)
    ada, _ = account(sessions, ADA)
    started = store.start(None, ada)
    usage = Usage(datetime.now(UTC), 1.5, 120, 8, "done")
    said = [
        Message(role="caller", content="When do you open?"),
        Message(role="desk", content="We open at 9."),
    ]
    store.keep(started.id, usage, said)
    assert store.get(started.id, ada).messages == said


@pytest.mark.id("tst_wcxoqb")
def test_a_person_goes_with_their_conversations(pool):
    """When a person is deleted, their conversations, messages and turns go too"""
    sessions, store = Sessions(pool), Store(pool)
    (ada, _), (grace, _) = account(sessions, ADA), account(sessions, GRACE)
    hers = store.start(None, ada)
    store.keep(
        hers.id,
        Usage(datetime.now(UTC), 1.0, 10, 2, "done"),
        [Message(role="caller", content="Hi"), Message(role="desk", content="Hello")],
    )
    kept = store.start(None, grace)
    with pool.connection() as conn:
        conn.execute("DELETE FROM people WHERE id = %s", [ada])
    assert [id for (id,) in rows(pool, "SELECT id FROM conversations")] == [kept.id]
    assert rows(pool, "SELECT count(*) FROM messages") == [(0,)]
    assert rows(pool, "SELECT count(*) FROM turns") == [(0,)]


@pytest.mark.id("tst_xfgfuy")
def test_the_routes_serve_each_person_their_own(loop, pool):
    """Through the routes, each person starts, lists and reads their own conversations, gets
    404 for someone else's, and a request without a session gets 403"""
    sessions = Sessions(pool)
    app = FastAPI()
    install(app)
    app.include_router(conversations_router)
    app.state.sessions = sessions
    app.state.conversations = Store(pool)
    (_, ada), (_, grace) = account(sessions, ADA), account(sessions, GRACE)

    def cookie(token):
        return {"Cookie": f"{SESSION_COOKIE}={token}"}

    async def go():
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="https://desk.test"
        ) as client:
            started = await client.post(
                "/conversations", json={"page": "va"}, headers=cookie(ada)
            )
            path = started.headers["location"]
            return (
                started,
                await client.get(path, headers=cookie(ada)),
                await client.get(path, headers=cookie(grace)),
                await client.get("/conversations", headers=cookie(ada)),
                await client.get("/conversations", headers=cookie(grace)),
                await client.get(path),
                await client.post("/conversations", json={}),
            )

    started, mine, theirs, ada_list, grace_list, anonymous, start = (
        loop.run_until_complete(go())
    )
    assert started.status_code == 201
    assert mine.json() == started.json()
    assert theirs.status_code == 404
    assert [each["id"] for each in ada_list.json()] == [started.json()["id"]]
    assert grace_list.json() == []
    assert (anonymous.status_code, start.status_code) == (403, 403)
