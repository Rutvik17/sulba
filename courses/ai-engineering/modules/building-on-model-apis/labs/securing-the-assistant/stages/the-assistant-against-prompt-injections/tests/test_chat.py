import sqlite3
from datetime import datetime

import pytest

from actions import Actions
from chat import INSTRUCTIONS, REPLY_TOKENS, Chat
from shop import SCHEMA

NOW = datetime(2026, 10, 20, 9, 0)
BOOKINGS = [
    (
        "B-1042",
        "C-7",
        "2026-10-24",
        "10:30",
        "brakes",
        "city",
        "Squeaks downhill.",
        "booked",
    ),
]


def shop():
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    db.executemany("INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?, ?)", BOOKINGS)
    return db


def chat(model, db):
    return Chat(model.client(), db, Actions(db), "C-7", lambda: NOW)


@pytest.mark.id("tst_yvvhwa")
def test_answers(model):
    """An answer comes back as HTML, asked with the shop's tools and its limit on a reply"""
    model.says("Find us at **12 Mill Lane**.")
    reply = chat(model, shop()).send("Where are you?")
    assert reply.html == "<p>Find us at <strong>12 Mill Lane</strong>.</p>"
    assert reply.actions == []
    [request] = model.requests
    assert request.body["messages"] == [
        {"role": "system", "content": INSTRUCTIONS},
        {"role": "user", "content": "Where are you?"},
    ]
    names = {tool["function"]["name"] for tool in request.body["tools"]}
    assert names == {"my_bookings", "booking", "reviews", "cancel_booking"}
    assert request.body["max_completion_tokens"] == REPLY_TOKENS


@pytest.mark.id("tst_xgnqgo")
def test_conversation(model):
    """A tool call runs, and the conversation goes on from where it was"""
    model.says(tool_calls=[("my_bookings", {})])
    model.says("You're booked for brakes on Saturday at 10:30.")
    model.says("Bring the bike in by 10:15.")
    talk = chat(model, shop())
    first = talk.send("When am I booked?")
    assert first.html == "<p>You&#x27;re booked for brakes on Saturday at 10:30.</p>"
    talk.send("When should I come?")
    messages = model.requests[2].body["messages"]
    assert [message["role"] for message in messages] == [
        "system",
        "user",
        "assistant",
        "tool",
        "assistant",
        "user",
    ]
    assert "B-1042" in messages[3]["content"]
    assert messages[4] == {
        "role": "assistant",
        "content": "You're booked for brakes on Saturday at 10:30.",
    }
