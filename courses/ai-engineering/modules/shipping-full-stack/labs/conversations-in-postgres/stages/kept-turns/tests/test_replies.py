import json
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import anyio
import anyio.lowlevel
import anyio.to_thread
import numpy as np
import psycopg
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from psycopg_pool import ConnectionPool

from agent import Agent
from conversations import install
from conversations import router as conversations_router
from desk import TICKETS, Actions, Desk, Search, free_times
from gate import Gate
from migrations import migrate
from replies import Agents
from replies import router as replies_router
from store import Store

PASSAGES = [
    {
        "passage": "p1",
        "page": "ssa-1",
        "domain": "ssa",
        "title": "Replacement cards | SSA",
        "text": "You can ask for a replacement card online.",
    }
]


@contextmanager
def desk_app(database, model, running=1, waiting=4, seconds=60):
    """The desk's app on a migrated database, its agents on the scripted model."""
    with psycopg.connect(database, autocommit=True) as conn:
        migrate(conn)
    with ConnectionPool(
        database, min_size=1, max_size=4, kwargs={"autocommit": True}, open=True
    ) as pool:
        client = model.async_client(timeout=300)
        desk = Desk(
            Search(client, PASSAGES, np.array([[1.0, 0.0]])), TICKETS, free_times()
        )
        app = FastAPI()
        install(app)
        app.include_router(conversations_router)
        app.include_router(replies_router)
        app.state.conversations = Store(pool)
        app.state.gate = Gate(running, waiting, seconds)
        app.state.agents = Agents(lambda page: Agent(client, Actions(desk), page))
        yield app, pool


def events(text):
    found = []
    for block in text.split("\n\n"):
        fields = dict(
            line.split(": ", 1) for line in block.splitlines() if ": " in line
        )
        if "event" in fields:
            found.append((fields["event"], json.loads(fields["data"])))
    return found


def client_for(app):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://desk.test")


def turns(pool):
    with pool.connection() as conn:
        return conn.execute(
            "SELECT started_at, seconds, prompt_tokens, completion_tokens, outcome "
            "FROM turns ORDER BY id"
        ).fetchall()


def say(loop, app, content="When do you open?"):
    async def go():
        async with client_for(app) as client:
            started = (await client.post("/conversations", json={})).json()["id"]
            reply = await client.post(
                f"/conversations/{started}/messages", json={"content": content}
            )
            kept = await client.get(f"/conversations/{started}")
            return reply, kept.json()

    return loop.run_until_complete(go())


@pytest.mark.id("tst_50arw7")
def test_a_turn_done(loop, database, model):
    """A turn that's done keeps its messages, and what it used: its seconds and tokens"""
    model.says("We open at 9.", after=12, usage=(900, 40))
    with desk_app(database, model) as (app, pool):
        before = datetime.now(UTC)
        reply, kept = say(loop, app)
        assert events(reply.text)[-1] == ("done", {"content": "We open at 9."})
        assert [m["content"] for m in kept["messages"]] == [
            "When do you open?",
            "We open at 9.",
        ]
        ((started_at, seconds, prompt, completion, outcome),) = turns(pool)
        assert before <= started_at <= datetime.now(UTC) + timedelta(seconds=1)
        assert (seconds, prompt, completion, outcome) == (12, 900, 40, "done")


@pytest.mark.id("tst_z1gasy")
def test_a_turn_too_long(loop, database, model):
    """A turn past its time keeps no messages, and keeps what it used before it stopped"""
    model.says(
        tool_calls=[("search_help", {"query": "hours", "service": "ssa"})],
        after=5,
        usage=(500, 20),
    )
    model.embeds(lambda text: [1.0, 0.0])
    model.hangs()
    with desk_app(database, model, seconds=60) as (app, pool):
        reply, kept = say(loop, app)
        assert events(reply.text)[-1] == (
            "error",
            {"title": "The reply took too long."},
        )
        assert kept["messages"] == []
        assert [row[1:] for row in turns(pool)] == [(60, 500, 20, "too long")]


@pytest.mark.id("tst_v2lfpt")
def test_a_turn_that_fails(loop, database, model):
    """A turn the model fails is kept as failed, with no messages"""
    model.fails(500, "The model's server stopped.")
    with desk_app(database, model) as (app, pool):
        reply, kept = say(loop, app)
        assert events(reply.text) == [("error", {"title": "The desk couldn't reply."})]
        assert kept["messages"] == []
        assert [row[4] for row in turns(pool)] == ["failed"]


@pytest.mark.id("tst_35qu6c")
def test_a_caller_who_leaves(loop, database, model, monkeypatch):
    """A caller who leaves mid-reply has the turn kept as left, and frees its place"""

    async def in_a_thread(func, *args, **_):
        # Handing work to a worker thread is a point where cancellation lands.
        await anyio.lowlevel.checkpoint()
        return func(*args)

    monkeypatch.setattr(anyio.to_thread, "run_sync", in_a_thread)
    model.says("Too late.", after=30)
    model.says("We open at 9.")
    with desk_app(database, model, running=1) as (app, pool):

        async def go():
            async with client_for(app) as client:
                started = (await client.post("/conversations", json={})).json()["id"]
                path = f"/conversations/{started}/messages"
                # The caller gives up after 10 seconds, and their request is cancelled.
                with anyio.move_on_after(10):
                    await client.post(path, json={"content": "Hello?"})
                return await client.post(path, json={"content": "Hello again"})

        again = loop.run_until_complete(go())
        assert events(again.text)[-1] == ("done", {"content": "We open at 9."})
        assert [(row[1], row[4]) for row in turns(pool)] == [(10, "left"), (0, "done")]
        assert app.state.agents.replying == set()


@pytest.mark.id("tst_1lugdh")
def test_messages_that_cannot_be_answered(loop, database, model):
    """A conversation that isn't in the database gets a 404, and keeps nothing"""
    with desk_app(database, model) as (app, pool):

        async def go():
            async with client_for(app) as client:
                return await client.post(
                    "/conversations/nope/messages", json={"content": "Hello"}
                )

        missing = loop.run_until_complete(go())
        assert missing.status_code == 404
        assert missing.headers["content-type"] == "application/problem+json"
        assert turns(pool) == []


@pytest.mark.id("tst_ak5rhe")
def test_a_conversation_from_an_earlier_run(loop, database, model):
    """A conversation kept by an earlier run of the app goes on from its messages"""
    model.says("We open at 9.")
    model.says("At 10 on Saturdays.")
    with desk_app(database, model) as (app, _):
        _, started = say(loop, app)
    # A new run: new agents on the same database.
    with desk_app(database, model) as (app, _):

        async def go():
            async with client_for(app) as client:
                path = f"/conversations/{started['id']}/messages"
                return await client.post(path, json={"content": "And Saturdays?"})

        reply = loop.run_until_complete(go())
    assert events(reply.text)[-1] == ("done", {"content": "At 10 on Saturdays."})
    read = [(m["role"], m["content"]) for m in model.requests[-1].body["messages"][1:]]
    assert read == [
        ("user", "When do you open?"),
        ("assistant", "We open at 9."),
        ("user", "And Saturdays?"),
    ]
