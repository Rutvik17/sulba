import json

import numpy as np
import pytest

from agent import OutOfRounds
from desk import Desk, Search
from desk_agent import DeskAgent

PASSAGES = [
    {
        "passage": "p1",
        "domain": "ssa",
        "title": "Get a Social Security card | SSA",
        "text": "Apply for a replacement card online or at an office.",
    },
]
FREE = {
    service: {"2026-11-03": ["10:00", "14:00"]} for service in ("ssa", "va", "studentaid", "dmv")
}
CARD = {"ticket": "T-2101", "service": "ssa", "status": "open", "summary": "Replacement card"}


def agent_for(model):
    model.embeds(lambda text: [1.0])
    desk = Desk(Search(model.client(), PASSAGES, np.array([[1]])), [CARD], FREE)
    return desk, DeskAgent(model.client(), desk, "ssa")


@pytest.mark.id("tst_7a4whz")
def test_a_turn_ends(model):
    """A model that keeps calling tools gets 8 requests a turn, then OutOfRounds"""
    for _ in range(9):
        model.says(tool_calls=[("list_tickets", {})])
    _, agent = agent_for(model)
    with pytest.raises(OutOfRounds):
        agent.reply("What tickets do I have?")
    assert len(model.requests) == 8


@pytest.mark.id("tst_emr0oh")
def test_results_follow_their_calls(model):
    """Each tool's result goes back after the model's message that called it, as the API
    requires"""
    model.says(tool_calls=[("list_tickets", {})])
    model.says("You have ticket T-2101.")
    _, agent = agent_for(model)
    agent.reply("What tickets do I have?")
    *_, called, result = model.requests[1].body["messages"]
    assert called["role"] == "assistant"
    assert [call["id"] for call in called["tool_calls"]] == [result["tool_call_id"]]


@pytest.mark.id("tst_0fw73v")
def test_arguments_that_arent_json(model):
    """Arguments that aren't JSON give the model an error, and the turn goes on"""
    model.says(tool_calls=[("book_callback", '{"ticket": "T-2101", "day": ')])
    model.says("Sorry, I couldn't book that.")
    desk, agent = agent_for(model)
    assert agent.reply("Book me in for Tuesday.") == "Sorry, I couldn't book that."
    result = model.requests[1].body["messages"][-1]
    assert list(json.loads(result["content"])) == ["error"]
    assert desk.writes == []


@pytest.mark.id("tst_qkr2u6")
def test_the_conversation_goes_on(model):
    """The caller's yes reaches the model with the offer it answers"""
    model.says("I can book T-2101 on Tuesday at 10:00. Shall I?")
    model.says("Booked.")
    _, agent = agent_for(model)
    agent.reply("Can someone call me Tuesday at 10?")
    agent.reply("Yes, please book it.")
    messages = model.requests[1].body["messages"]
    assert [message["role"] for message in messages] == ["system", "user", "assistant", "user"]
    assert messages[2]["content"] == "I can book T-2101 on Tuesday at 10:00. Shall I?"
