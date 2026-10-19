import json
from typing import Literal

import pytest

from loop import MODEL, ModelError, NoAnswer, answer
from tools import describe

Day = Literal[
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]
Service = Literal["puncture", "brakes", "gears", "full service"]
QUESTION = [
    {
        "role": "system",
        "content": "You answer for a bicycle repair shop. Use its tools.",
    },
    {
        "role": "user",
        "content": "When are you open on Saturday, and what are new brakes?",
    },
]


def opening_hours(day: Day) -> str:
    """The shop's opening hours on a day of the week."""
    hours = {"Saturday": "9:00 to 13:00", "Sunday": "Closed"}
    return hours.get(day, "9:00 to 17:00")


def repair_price(service: Service, bikes: int) -> float:
    """The price of a repair, in pounds."""
    if bikes < 1:
        raise ValueError("A repair is for one bike or more.")
    return {"puncture": 12.0, "brakes": 18.0, "gears": 25.0, "full service": 60.0}[
        service
    ] * bikes


SHOP = [opening_hours, repair_price]


def tool_results(request):
    return [
        (message["tool_call_id"], json.loads(message["content"]))
        for message in request.body["messages"]
        if message["role"] == "tool"
    ]


@pytest.mark.id("tst_yji6wl")
def test_no_tools_needed(model):
    """An answer that calls no tool comes back as it is, after one request with the tools"""
    model.says("We're at 12 Mill Lane.")
    assert answer(model.client(), QUESTION, SHOP) == "We're at 12 Mill Lane."
    [request] = model.requests
    assert request.body["model"] == MODEL
    assert request.body["messages"] == QUESTION
    assert request.body["tools"] == [describe(opening_hours), describe(repair_price)]


@pytest.mark.id("tst_an3lzl")
def test_one_call(model):
    """A tool call runs, and its result goes back with the model's call before it"""
    model.says(tool_calls=[("opening_hours", {"day": "Saturday"})])
    model.says("We're open 9:00 to 13:00 on Saturdays.")
    assert (
        answer(model.client(), QUESTION, SHOP)
        == "We're open 9:00 to 13:00 on Saturdays."
    )
    messages = model.requests[1].body["messages"]
    assert messages[:2] == QUESTION
    assert messages[2]["role"] == "assistant"
    [called] = messages[2]["tool_calls"]
    assert (called["id"], called["function"]["name"]) == ("call_1", "opening_hours")
    assert messages[3] == {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": json.dumps("9:00 to 13:00"),
    }


@pytest.mark.id("tst_4c7um9")
def test_parallel_calls(model):
    """Each of several calls in one reply runs, and each result goes back with its call's id"""
    model.says(
        tool_calls=[
            ("opening_hours", {"day": "Saturday"}),
            ("repair_price", {"service": "brakes", "bikes": 1}),
        ]
    )
    model.says("Saturdays 9:00 to 13:00, and new brakes are £18.")
    answer(model.client(), QUESTION, SHOP)
    assert len(model.requests) == 2
    assert tool_results(model.requests[1]) == [
        ("call_1", "9:00 to 13:00"),
        ("call_2", 18.0),
    ]


@pytest.mark.id("tst_46lao6")
def test_tool_errors(model):
    """A call that fails goes back as an error, and the model can call again"""
    model.says(tool_calls=[("repair_price", {"service": "brakes", "bikes": 0})])
    model.says(tool_calls=[("repair_price", {"service": "brakes", "bikes": 1})])
    model.says("New brakes are £18.")
    assert answer(model.client(), QUESTION, SHOP) == "New brakes are £18."
    assert tool_results(model.requests[1]) == [
        ("call_1", {"error": "A repair is for one bike or more."})
    ]
    assert tool_results(model.requests[2])[-1] == ("call_2", 18.0)


@pytest.mark.id("tst_93nke0")
def test_rounds(model):
    """A model that keeps calling tools gets no more than its rounds of requests"""
    model.answers(
        lambda request: model.says(tool_calls=[("opening_hours", {"day": "Monday"})])
    )
    with pytest.raises(NoAnswer):
        answer(model.client(), QUESTION, SHOP, rounds=3)
    assert len(model.requests) == 3


@pytest.mark.id("tst_85u3h3")
def test_no_answer(model):
    """A reply cut off at its limit is no answer, and the API's errors are raised"""
    model.says("We're open 9:00 to", finish_reason="length")
    with pytest.raises(NoAnswer):
        answer(model.client(), QUESTION, SHOP)
    model.fails(503, "Loading model")
    with pytest.raises(ModelError) as raised:
        answer(model.client(), QUESTION, SHOP)
    assert (raised.value.status, raised.value.message) == (503, "Loading model")
