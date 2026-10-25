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


@pytest.mark.id("tst_9kh92l")
def test_a_missing_conversation_takes_no_place(loop, model):
    """A message to a conversation that isn't there gets a 404 without taking a place at the
    gate"""
    model.says("We open at 9.")
    app = make_app(model, running=1)
    conversation = start(loop, app)
    (missing,) = send(
        loop, app, ("POST", "/conversations/nope/messages", {"content": "Hi"})
    )
    assert missing.status_code == 404
    (reply,) = send(
        loop,
        app,
        ("POST", f"/conversations/{conversation}/messages", {"content": "Hi"}),
    )
    assert events(reply.text)[-1] == ("done", {"content": "We open at 9."})


@pytest.mark.id("tst_l5gc9f")
def test_a_failed_reply_frees_its_place(loop, model):
    """A reply the model fails ends in an error event and frees its place at the gate"""
    model.fails(500, "The model's server stopped.")
    model.says("We open at 9.")
    app = make_app(model, running=1)
    conversation = start(loop, app)
    path = f"/conversations/{conversation}/messages"
    (failed,) = send(loop, app, ("POST", path, {"content": "Hi"}))
    assert events(failed.text) == [("error", {"title": "The desk couldn't reply."})]
    (reply,) = send(loop, app, ("POST", path, {"content": "Hi"}))
    assert events(reply.text)[-1] == ("done", {"content": "We open at 9."})


@pytest.mark.id("tst_0gnhf2")
def test_a_yes_to_a_proposal(loop, model):
    """The caller's yes makes the callback the desk proposed in the same conversation"""
    model.says(
        tool_calls=[
            (
                "propose_callback",
                {"service": "ssa", "day": "2026-11-03", "time": "10:00"},
            )
        ]
    )
    model.says("Shall I book it?")
    model.says("It's booked.")
    app = make_app(model)
    conversation = start(loop, app)
    path = f"/conversations/{conversation}/messages"
    send(loop, app, ("POST", path, {"content": "Call me Tuesday at 10"}))
    send(loop, app, ("POST", path, {"content": "Yes please"}))
    assert app.state.desk.callbacks == [
        {"ticket": "T-2041", "day": "2026-11-03", "time": "10:00"}
    ]


@pytest.mark.id("tst_ugth4x")
def test_a_model_that_never_answers(loop, model):
    """A reply the model never sends ends in an error event at the time limit"""
    model.hangs()
    app = make_app(model, seconds=45)
    conversation = start(loop, app)
    (reply,) = send(
        loop,
        app,
        ("POST", f"/conversations/{conversation}/messages", {"content": "Hi"}),
    )
    assert events(reply.text) == [("error", {"title": "The reply took too long."})]
    assert loop.time() == pytest.approx(45)
