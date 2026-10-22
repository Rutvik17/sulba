import asyncio
import json

import numpy as np
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from agent import Agent
from conversations import Conversations, install
from conversations import router as conversations_router
from desk import TICKETS, Actions, Desk, Search, free_times
from gate import Gate
from replies import Agents
from replies import router as replies_router

PASSAGES = [
    {
        "passage": "p1",
        "page": "ssa-1",
        "domain": "ssa",
        "title": "Replacement cards | SSA",
        "text": "You can ask for a replacement card online.",
    },
    {
        "passage": "p2",
        "page": "dmv-1",
        "domain": "dmv",
        "title": "Licenses | DMV",
        "text": "Renew a license at a DMV office.",
    },
]


def make_app(model, running=1, waiting=4, seconds=60):
    """The desk's app, its agents on the scripted model, which may take minutes to reply."""
    client = model.async_client(timeout=300)
    desk = Desk(
        Search(client, PASSAGES, np.array([[1, 0], [0, 1]])), TICKETS, free_times()
    )
    app = FastAPI()
    install(app)
    app.include_router(conversations_router)
    app.include_router(replies_router)
    app.state.conversations = Conversations()
    app.state.gate = Gate(running, waiting, seconds)
    app.state.agents = Agents(lambda page: Agent(client, Actions(desk), page))
    return app


def events(text):
    """Each event in a stream of server-sent events, as (event, data)."""
    found = []
    for block in text.split("\n\n"):
        fields = dict(
            line.split(": ", 1) for line in block.splitlines() if ": " in line
        )
        if "event" in fields:
            found.append((fields["event"], json.loads(fields["data"])))
    return found


async def call(app, *requests):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://desk.test") as client:
        return await asyncio.gather(
            *(
                client.request(method, path, json=body)
                for method, path, body in requests
            )
        )


def start(loop, app, page=None):
    (response,) = loop.run_until_complete(
        call(app, ("POST", "/conversations", {"page": page}))
    )
    return response.json()["id"]


@pytest.mark.id("tst_h7w4ky")
def test_a_streamed_reply(loop, model):
    """The reply as it comes, each tool the desk runs, then the whole reply, which the
    conversation keeps with the caller's message"""
    model.embeds(lambda text: [1.0, 0.0])
    model.says(tool_calls=[("search_help", {"query": "lost card", "service": "ssa"})])
    model.says("Ask for one ", "online [p1].")
    app = make_app(model)
    conversation = start(loop, app, "ssa")
    path = f"/conversations/{conversation}/messages"
    (response,) = loop.run_until_complete(
        call(app, ("POST", path, {"content": " I lost my card "}))
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert events(response.text) == [
        ("tool", {"name": "search_help"}),
        ("text", {"delta": "Ask for one "}),
        ("text", {"delta": "online [p1]."}),
        ("done", {"content": "Ask for one online [p1]."}),
    ]
    (kept,) = loop.run_until_complete(
        call(app, ("GET", f"/conversations/{conversation}", None))
    )
    assert kept.json()["messages"] == [
        {"role": "caller", "content": "I lost my card"},
        {"role": "desk", "content": "Ask for one online [p1]."},
    ]


@pytest.mark.id("tst_4gvsx9")
def test_messages_that_cannot_be_answered(loop, model):
    """A conversation that isn't there or a message that doesn't fit gets a problem details
    object, and takes no place at the gate"""
    app = make_app(model)
    conversation = start(loop, app)
    path = f"/conversations/{conversation}/messages"
    missing, empty, long, extra = loop.run_until_complete(
        call(
            app,
            ("POST", "/conversations/nope/messages", {"content": "Hello"}),
            ("POST", path, {"content": "   "}),
            ("POST", path, {"content": "x" * 2001}),
            ("POST", path, {"content": "Hello", "page": "dmv"}),
        )
    )
    assert missing.status_code == 404
    assert missing.headers["content-type"] == "application/problem+json"
    for response, at in ((empty, "#/content"), (long, "#/content"), (extra, "#/page")):
        assert response.status_code == 422
        assert [error["pointer"] for error in response.json()["errors"]] == [at]
    assert app.state.gate.queued == 0 and not app.state.gate.places.locked()
    assert app.state.agents.replying == set()


@pytest.mark.id("tst_bco72h")
def test_a_full_line(loop, model):
    """Past the line's end, a 503 that says when to come back"""
    model.says("One.", after=30)
    model.says("Two.", after=30)
    app = make_app(model, running=1, waiting=1, seconds=60)
    first, second, third = (start(loop, app) for _ in range(3))
    replies = loop.run_until_complete(
        call(
            app,
            *(
                ("POST", f"/conversations/{each}/messages", {"content": "Hello"})
                for each in (first, second, third)
            ),
        )
    )
    assert [reply.status_code for reply in replies] == [200, 200, 503]
    assert replies[2].headers["retry-after"] == "60"
    assert replies[2].json()["title"] == "Service Unavailable"
    assert events(replies[1].text)[-1] == ("done", {"content": "Two."})


@pytest.mark.id("tst_2jy1rv")
def test_a_reply_past_its_time(loop, model):
    """A reply past its time limit ends in an error event, keeps nothing, and frees its place"""
    model.says("Too late.", after=90)
    model.says("In time.")
    app = make_app(model, seconds=60)
    conversation = start(loop, app)
    path = f"/conversations/{conversation}/messages"
    (late,) = loop.run_until_complete(call(app, ("POST", path, {"content": "Hello"})))
    assert events(late.text) == [("error", {"title": "The reply took too long."})]
    (again,) = loop.run_until_complete(
        call(app, ("POST", path, {"content": "Hello again"}))
    )
    assert events(again.text)[-1] == ("done", {"content": "In time."})
    (kept,) = loop.run_until_complete(
        call(app, ("GET", f"/conversations/{conversation}", None))
    )
    assert [message["content"] for message in kept.json()["messages"]] == [
        "Hello again",
        "In time.",
    ]
    # The agent forgot the turn that failed too, so the model never reads it.
    assert [each["content"] for each in model.requests[-1].body["messages"][1:]] == [
        "Hello again"
    ]


@pytest.mark.id("tst_6zhzx7")
def test_one_reply_at_a_time(loop, model):
    """A second message while the desk is still replying in the conversation gets a 409"""
    model.says("First.", after=10)
    app = make_app(model, running=2)
    conversation = start(loop, app)
    path = f"/conversations/{conversation}/messages"
    first, second = loop.run_until_complete(
        call(
            app, ("POST", path, {"content": "One"}), ("POST", path, {"content": "Two"})
        )
    )
    assert first.status_code == 200
    assert second.status_code == 409
    assert second.headers["content-type"] == "application/problem+json"
    assert app.state.agents.replying == set()
