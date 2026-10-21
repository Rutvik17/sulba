import json

import numpy as np
import pytest

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


@pytest.mark.id("tst_8g1avn")
def test_a_reply(model):
    """A reply with no tool calls comes back as it is"""
    model.says("Hello! How can I help?")
    _, agent = agent_for(model)
    assert agent.reply("Hi") == "Hello! How can I help?"
    assert model.requests[0].body["messages"][-1] == {"role": "user", "content": "Hi"}


@pytest.mark.id("tst_l98p11")
def test_a_tool_result_reaches_the_model(model):
    """The result of a tool the model calls is in the next request"""
    model.says(tool_calls=[("list_tickets", {})])
    model.says("You have ticket T-2101.")
    _, agent = agent_for(model)
    assert agent.reply("What tickets do I have?") == "You have ticket T-2101."
    result = model.requests[1].body["messages"][-1]
    assert result["role"] == "tool"
    assert json.loads(result["content"])["tickets"][0]["ticket"] == "T-2101"


@pytest.mark.id("tst_yf12qx")
def test_requests_are_kept(model):
    """Each request is kept with its tokens and the tools it called"""
    model.says(tool_calls=[("list_tickets", {})], usage=(900, 10))
    model.says("You have ticket T-2101.", usage=(1000, 8))
    _, agent = agent_for(model)
    agent.reply("What tickets do I have?")
    assert [(made.prompt_tokens, made.calls) for made in agent.requests] == [
        (900, ("list_tickets",)),
        (1000, ()),
    ]
