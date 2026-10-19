import json

import pytest

from assistant import INSTRUCTIONS, SORRY, Assistant, opening_hours, repair_price
from tools import describe


@pytest.mark.id("tst_n009ci")
def test_answers(model):
    """An answer that needs no tool comes back, asked with the shop's tools"""
    model.says("We're at 12 Mill Lane.")
    assert (
        Assistant(model.client()).answer("Where are you?") == "We're at 12 Mill Lane."
    )
    [request] = model.requests
    assert request.body["messages"] == [
        {"role": "system", "content": INSTRUCTIONS},
        {"role": "user", "content": "Where are you?"},
    ]
    assert request.body["tools"] == [describe(opening_hours), describe(repair_price)]


@pytest.mark.id("tst_d8wbee")
def test_uses_a_tool(model):
    """A tool the model calls runs, and the model answers with its result"""
    model.says(tool_calls=[("opening_hours", {"day": "Saturday"})])
    model.says("We're open 9:00 to 13:00 on Saturdays.")
    found = Assistant(model.client()).answer("When are you open on Saturday?")
    assert found == "We're open 9:00 to 13:00 on Saturdays."
    assert model.requests[1].body["messages"][-1] == {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": json.dumps("9:00 to 13:00"),
    }


@pytest.mark.id("tst_b75wxz")
def test_no_answer(model):
    """A customer gets SORRY when the model can't answer"""
    model.fails(503, "Loading model")
    assert Assistant(model.client()).answer("Where are you?") == SORRY
    model.says("We're at", finish_reason="length")
    assert Assistant(model.client()).answer("Where are you?") == SORRY
