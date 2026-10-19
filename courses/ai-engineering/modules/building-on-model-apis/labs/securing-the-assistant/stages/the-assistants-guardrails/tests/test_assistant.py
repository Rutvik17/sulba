import json
import sqlite3
from datetime import datetime

import pytest

from actions import Actions
from assistant import INSTRUCTIONS, Assistant
from shop import SCHEMA

NOW = datetime(2026, 10, 20, 9, 0)
BOOKINGS = [
    ("B-1042", "C-7", "2026-10-24", "10:30", "brakes", "city", "", "booked"),
    (
        "B-2001",
        "C-9",
        "2026-10-24",
        "11:00",
        "full service",
        "cargo",
        "Gate code 4417.",
        "booked",
    ),
]


def shop():
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    db.executemany("INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?, ?)", BOOKINGS)
    return db


def assistant(model, db):
    return Assistant(model.client(), db, Actions(db), "C-7", lambda: NOW)


@pytest.mark.id("tst_lxwaa1")
def test_answers(model):
    """An answer comes back as HTML, asked with the shop's tools"""
    model.says("Find us at **12 Mill Lane**.")
    reply = assistant(model, shop()).answer("Where are you?")
    assert reply.html == "<p>Find us at <strong>12 Mill Lane</strong>.</p>"
    assert reply.actions == []
    [request] = model.requests
    assert request.body["messages"] == [
        {"role": "system", "content": INSTRUCTIONS},
        {"role": "user", "content": "Where are you?"},
    ]
    names = [tool["function"]["name"] for tool in request.body["tools"]]
    assert {
        "my_bookings",
        "booking",
        "reviews",
        "taken_times",
        "cancel_booking",
    } <= set(names)


@pytest.mark.id("tst_724hll")
def test_taken_times(model):
    """The times already booked on a day reach the model"""
    model.says(tool_calls=[("taken_times", {"day": "2026-10-24"})])
    model.says("10:30 and 11:00 are taken.")
    reply = assistant(model, shop()).answer("What's free on Saturday the 24th?")
    assert reply.html == "<p>10:30 and 11:00 are taken.</p>"
    content = model.requests[1].body["messages"][-1]["content"]
    assert "10:30" in content and "11:00" in content


@pytest.mark.id("tst_sl9xeu")
def test_cancelling_waits(model):
    """A cancellation waits for the customer's button"""
    db = shop()
    model.says(tool_calls=[("cancel_booking", {"reference": "B-1042"})])
    model.says("Please confirm below.")
    bot = assistant(model, db)
    reply = bot.answer("Cancel my brakes booking.")
    [action] = reply.actions
    assert action.question == "Cancel booking B-1042, brakes on 2026-10-24 at 10:30?"
    status = "SELECT status FROM bookings WHERE reference = 'B-1042'"
    assert db.execute(status).fetchone() == ("booked",)
    assert bot.confirm(action.id).html == "<p>Booking B-1042 is cancelled.</p>"
    assert db.execute(status).fetchone() == ("cancelled",)
    assert (
        json.loads(model.requests[1].body["messages"][-1]["content"])[
            "waiting_for_the_customer"
        ]
        == action.question
    )
