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
from desk_replies import Agents
from desk_replies import router as replies_router
from gate import Gate

PASSAGES = [
    {
        "passage": "p1",
        "page": "ssa-1",
        "domain": "ssa",
        "title": "Replacement cards | SSA",
        "text": "You can ask for a replacement card online.",
    },
]


def make_app(model, running=1, waiting=4, seconds=60):
    client = model.async_client(timeout=300)
    desk = Desk(Search(client, PASSAGES, np.array([[1, 0]])), TICKETS, free_times())
    app = FastAPI()
    install(app)
    app.include_router(conversations_router)
    app.include_router(replies_router)
    app.state.conversations = Conversations()
    app.state.gate = Gate(running, waiting, seconds)
    app.state.agents = Agents(lambda page: Agent(client, Actions(desk), page))
    app.state.desk = desk
    return app


def events(text):
    found = []
    for block in text.split("\n\n"):
        fields = dict(
            line.split(": ", 1) for line in block.splitlines() if ": " in line
        )
        if "event" in fields:
            found.append((fields["event"], json.loads(fields["data"])))
    return found


def send(loop, app, *requests):
    async def go():
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://desk.test"
        ) as client:
            return await asyncio.gather(
                *(
                    client.request(method, path, json=body)
                    for method, path, body in requests
                )
            )

    return loop.run_until_complete(go())


def start(loop, app):
    (response,) = send(loop, app, ("POST", "/conversations", {}))
    return response.json()["id"]


@pytest.mark.id("tst_z4zp41")
def test_a_reply(loop, model):
    """The reply comes as text events, then a done event"""
    model.says("We open ", "at 9.")
    app = make_app(model)
    conversation = start(loop, app)
    (reply,) = send(
        loop,
        app,
        ("POST", f"/conversations/{conversation}/messages", {"content": "Hi"}),
    )
    assert events(reply.text) == [
        ("text", {"delta": "We open "}),
        ("text", {"delta": "at 9."}),
        ("done", {"content": "We open at 9."}),
    ]


@pytest.mark.id("tst_3tezqz")
def test_replies_one_after_another(loop, model):
    """With one place at the gate, two conversations' replies both come"""
    model.says("One.", after=5)
    model.says("Two.", after=5)
    app = make_app(model, running=1)
    first, second = start(loop, app), start(loop, app)
    replies = send(
        loop,
        app,
        ("POST", f"/conversations/{first}/messages", {"content": "Hi"}),
        ("POST", f"/conversations/{second}/messages", {"content": "Hi"}),
    )
    assert [events(reply.text)[-1] for reply in replies] == [
        ("done", {"content": "One."}),
        ("done", {"content": "Two."}),
    ]


@pytest.mark.id("tst_k6jhp7")
def test_an_empty_message(loop, model):
    """An empty message gets a 422"""
    app = make_app(model)
    conversation = start(loop, app)
    (reply,) = send(
        loop, app, ("POST", f"/conversations/{conversation}/messages", {"content": ""})
    )
    assert reply.status_code == 422


@pytest.mark.id("tst_o1xxhe")
def test_the_conversation_keeps_the_turn(loop, model):
    """The conversation keeps the caller's message and the reply"""
    model.says("We open at 9.")
    app = make_app(model)
    conversation = start(loop, app)
    send(
        loop,
        app,
        ("POST", f"/conversations/{conversation}/messages", {"content": "When?"}),
    )
    (kept,) = send(loop, app, ("GET", f"/conversations/{conversation}", None))
    assert [each["content"] for each in kept.json()["messages"]] == [
        "When?",
        "We open at 9.",
    ]
