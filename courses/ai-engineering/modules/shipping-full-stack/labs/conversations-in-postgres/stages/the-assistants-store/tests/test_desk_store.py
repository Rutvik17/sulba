from contextlib import contextmanager
from datetime import UTC, datetime

import psycopg
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from psycopg_pool import ConnectionPool

from conversations import Message, install, router
from desk_store import DeskStore
from migrations import migrate
from store import Usage

NOW = datetime(2026, 10, 22, 9, 30, tzinfo=UTC)


@contextmanager
def opened(database, size=4, timeout=30):
    """A store on a pool of autocommit connections to the database, migrated."""
    with psycopg.connect(database, autocommit=True) as conn:
        migrate(conn)
    with ConnectionPool(
        database,
        min_size=1,
        max_size=size,
        timeout=timeout,
        kwargs={"autocommit": True},
        open=True,
    ) as pool:
        yield DeskStore(pool), pool


def usage(outcome="done"):
    return Usage(NOW, 4.5, 1200, 80, outcome)


def turn(caller, desk):
    return [Message(role="caller", content=caller), Message(role="desk", content=desk)]


def send(loop, store, *requests):
    app = FastAPI()
    install(app)
    app.include_router(router)
    app.state.conversations = store

    async def go():
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://desk.test"
        ) as client:
            return [
                await client.request(method, path, json=body)
                for method, path, body in requests
            ]

    return loop.run_until_complete(go())


@pytest.mark.id("tst_5yt6y8")
def test_a_conversation_kept(database):
    """A conversation's turns come back in order"""
    with opened(database) as (store, _):
        conversation = store.start("dmv").id
        store.keep(conversation, usage(), turn("When do you open?", "At 9."))
        store.keep(conversation, usage(), turn("And Saturdays?", "At 10."))
        got = store.get(conversation)
        assert got is not None
        assert [m.content for m in got.messages] == [
            "When do you open?",
            "At 9.",
            "And Saturdays?",
            "At 10.",
        ]


@pytest.mark.id("tst_betwkp")
def test_a_missing_conversation(database):
    """A conversation that isn't there is None"""
    with opened(database) as (store, _):
        assert store.get("nope") is None


@pytest.mark.id("tst_xxng3f")
def test_usage_kept(database):
    """Each turn's usage is kept"""
    with opened(database) as (store, pool):
        conversation = store.start(None).id
        store.keep(conversation, usage(), turn("Hi", "Hello."))
        with pool.connection() as conn:
            rows = conn.execute("SELECT outcome FROM turns").fetchall()
        assert rows == [("done",)]


@pytest.mark.id("tst_taacv9")
def test_the_routes(loop, database):
    """The conversations' routes work on the store"""
    with opened(database) as (store, _):
        (started,) = send(loop, store, ("POST", "/conversations", {"page": "va"}))
        (got,) = send(loop, store, ("GET", started.headers["location"], None))
        assert got.json()["page"] == "va"
