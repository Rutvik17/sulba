import threading
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


@pytest.mark.id("tst_ikyf0s")
def test_an_id_that_is_not_one(loop, database):
    """An id written to look like SQL reads no one's conversation"""
    with opened(database) as (store, _):
        store.start("ssa")
        (got,) = send(loop, store, ("GET", "/conversations/x' OR 'x'='x", None))
        assert got.status_code == 404


@pytest.mark.id("tst_jmdx41")
def test_turns_kept_at_once(database):
    """Turns kept at once in one conversation are all kept"""
    with opened(database) as (store, _):
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
        assert got is not None and len(got.messages) == 40


@pytest.mark.id("tst_j90z6g")
def test_a_turn_that_cannot_be_kept(database):
    """A turn whose usage is refused keeps none of its messages"""
    with opened(database) as (store, _):
        conversation = store.start(None).id
        with pytest.raises(psycopg.errors.CheckViolation):
            store.keep(conversation, usage("cancelled"), turn("Hi", "Hello."))
        got = store.get(conversation)
        assert got is not None and got.messages == []


@pytest.mark.id("tst_157xv7")
def test_many_missing_conversations(loop, database):
    """Requests for conversations that aren't there don't use up the pool's connections"""
    with opened(database, size=2, timeout=1) as (store, _):
        started = store.start(None).id
        responses = send(
            loop,
            store,
            *[("GET", "/conversations/nope", None)] * 3,
            ("GET", f"/conversations/{started}", None),
        )
        assert [r.status_code for r in responses] == [404, 404, 404, 200]
