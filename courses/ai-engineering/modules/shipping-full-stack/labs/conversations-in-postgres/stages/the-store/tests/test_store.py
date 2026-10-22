import threading
from contextlib import contextmanager
from datetime import UTC, datetime

import psycopg
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from psycopg_pool import ConnectionPool

from conversations import Message, install, router
from migrations import migrate
from store import Store, Usage

NOW = datetime(2026, 10, 22, 9, 30, tzinfo=UTC)


@contextmanager
def opened(database, size=4):
    """A pool of autocommit connections to the database, migrated."""
    with psycopg.connect(database, autocommit=True) as conn:
        migrate(conn)
    with ConnectionPool(
        database, min_size=1, max_size=size, kwargs={"autocommit": True}, open=True
    ) as pool:
        yield pool


def usage(outcome="done", seconds=4.5):
    return Usage(NOW, seconds, 1200, 80, outcome)


def turn(caller, desk):
    return [Message(role="caller", content=caller), Message(role="desk", content=desk)]


@pytest.mark.id("tst_k985e1")
def test_a_conversation_kept(database):
    """A conversation started, its turns kept, and read back with its messages in order"""
    with opened(database) as pool:
        store = Store(pool)
        started = store.start("dmv")
        assert started.page == "dmv" and started.messages == []
        assert len(started.id) >= 22
        store.keep(started.id, usage(), turn("When do you open?", "At 9."))
        store.keep(started.id, usage(), turn("And Saturdays?", "At 10."))
        got = store.get(started.id)
        assert got is not None
        assert got.page == "dmv"
        assert [m.content for m in got.messages] == [
            "When do you open?",
            "At 9.",
            "And Saturdays?",
            "At 10.",
        ]
        assert [m.role for m in got.messages] == ["caller", "desk", "caller", "desk"]
        assert store.get("nope") is None


@pytest.mark.id("tst_vl6lbn")
def test_what_a_turn_used(database):
    """Each turn's usage is kept, a failed turn's with no messages"""
    with opened(database) as pool:
        store = Store(pool)
        conversation = store.start(None).id
        store.keep(conversation, usage("done", 4.5), turn("Hi", "Hello."))
        store.keep(conversation, usage("too long", 120.0))
        with pool.connection() as conn:
            rows = conn.execute(
                "SELECT started_at, seconds, prompt_tokens, completion_tokens, outcome "
                "FROM turns ORDER BY id"
            ).fetchall()
            messages = conn.execute("SELECT count(*) FROM messages").fetchone()
        assert rows == [
            (NOW, 4.5, 1200, 80, "done"),
            (NOW, 120.0, 1200, 80, "too long"),
        ]
        assert messages == (2,)


@pytest.mark.id("tst_k1fdzb")
def test_all_or_none(database):
    """A turn that can't be kept leaves nothing of itself behind"""
    with opened(database) as pool:
        store = Store(pool)
        conversation = store.start(None).id
        with pytest.raises(psycopg.errors.CheckViolation):
            store.keep(conversation, usage("cancelled"), turn("Hi", "Hello."))
        with pytest.raises(KeyError):
            store.keep("nope", usage(), turn("Hi", "Hello."))
        got = store.get(conversation)
        assert got is not None and got.messages == []
        with pool.connection() as conn:
            assert conn.execute("SELECT count(*) FROM turns").fetchone() == (0,)


@pytest.mark.id("tst_ay9etg")
def test_text_as_it_was_written(database):
    """Messages come back exactly as they were written, quotes and all"""
    written = 'It\'s "fine"; DROP TABLE messages; -- 100% ✓\nNext line'
    with opened(database) as pool:
        store = Store(pool)
        conversation = store.start("va").id
        store.keep(conversation, usage(), turn(written, "Noted."))
        got = store.get(conversation)
        assert got is not None and got.messages[0].content == written


@pytest.mark.id("tst_t2rrag")
def test_turns_kept_at_once(database):
    """Turns kept at once in one conversation each keep their two messages together"""
    with opened(database) as pool:
        store = Store(pool)
        conversation = store.start(None).id
        errors = []

        def keep(n):
            try:
                for k in range(5):
                    store.keep(conversation, usage(), turn(f"q{n}.{k}", f"a{n}.{k}"))
            except Exception as error:
                errors.append(error)

        threads = [threading.Thread(target=keep, args=(n,)) for n in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert errors == []
        got = store.get(conversation)
        assert got is not None
        contents = [m.content for m in got.messages]
        assert len(contents) == 40
        pairs = list(zip(contents[::2], contents[1::2], strict=True))
        assert all(q[1:] == a[1:] for q, a in pairs)


@pytest.mark.id("tst_qi37wa")
def test_the_routes_on_the_store(loop, database):
    """The conversations' routes work on the store as they did in memory"""
    with opened(database) as pool:
        app = FastAPI()
        install(app)
        app.include_router(router)
        app.state.conversations = Store(pool)

        async def go():
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://desk.test"
            ) as client:
                started = await client.post("/conversations", json={"page": "ssa"})
                got = await client.get(started.headers["location"])
                missing = await client.get("/conversations/nope")
                return started, got, missing

        started, got, missing = loop.run_until_complete(go())
        assert started.status_code == 201
        assert got.json() == {"id": started.json()["id"], "page": "ssa", "messages": []}
        assert missing.status_code == 404
