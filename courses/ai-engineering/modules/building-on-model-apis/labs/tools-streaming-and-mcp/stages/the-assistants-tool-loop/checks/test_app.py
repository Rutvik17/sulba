import json

import pytest

import assistant
from assistant import ROUNDS, SORRY, Assistant


@pytest.mark.id("tst_knmhyk")
def test_rounds(model):
    """A model that keeps calling tools gets no more than the assistant's rounds"""

    def keeps_calling(request):
        if len(model.requests) <= 20:
            model.says(tool_calls=[("opening_hours", {"day": "Monday"})])

    model.answers(keeps_calling)
    assert Assistant(model.client()).answer("Are you open on Monday?") == SORRY
    assert len(model.requests) == ROUNDS


@pytest.mark.id("tst_nsxzdt")
def test_each_result_to_its_call(model):
    """Every call in a reply runs, and its result goes back with its id"""
    model.says(
        tool_calls=[
            ("opening_hours", {"day": "Saturday"}),
            ("opening_hours", {"day": "Sunday"}),
        ]
    )
    model.says("Saturdays 9:00 to 13:00, and we're closed on Sundays.")
    Assistant(model.client()).answer("When are you open at the weekend?")
    results = [
        (message["tool_call_id"], json.loads(message["content"]))
        for message in model.requests[1].body["messages"]
        if message["role"] == "tool"
    ]
    assert results == [("call_1", "9:00 to 13:00"), ("call_2", "Closed")]


@pytest.mark.id("tst_4rd5s6")
def test_tool_errors(model):
    """A tool that fails tells the model why, and the model can still answer"""
    model.says(tool_calls=[("repair_price", {"service": "brakes", "bikes": 0})])
    model.says("New brakes are £18 a bike.")
    found = Assistant(model.client()).answer("How much are new brakes for no bikes?")
    assert found == "New brakes are £18 a bike."
    tool = model.requests[1].body["messages"][-1]
    assert json.loads(tool["content"]) == {"error": "A repair is for one bike or more."}


@pytest.mark.id("tst_rtokdk")
def test_only_offered_tools(model):
    """The model can run only the tools it was offered"""
    assistant.REFUNDS.clear()
    model.says(tool_calls=[("refund", {"booking": "B-1042", "amount": 60})])
    model.says("I can't refund that, but the shop can.")
    try:
        Assistant(model.client()).answer("Refund my full service, booking B-1042.")
    except Exception:
        pass
    assert assistant.REFUNDS == []
