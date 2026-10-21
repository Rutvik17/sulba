import json

import numpy as np
import pytest

from agent import SYSTEM, Agent, OutOfRounds, Request
from desk import Desk, Search, tools
from workflow import MODEL, SAMPLING

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


def agent_for(model, page="ssa", **options):
    model.embeds(lambda text: [1.0])
    desk = Desk(Search(model.client(), PASSAGES, np.array([[1]])), [CARD], FREE)
    return desk, Agent(model.client(), desk, page, **options)


def sent(request, role):
    return [message for message in request.body["messages"] if message["role"] == role]


@pytest.mark.id("tst_ejvir8")
def test_a_reply(model):
    """A reply with no tool calls comes back as it is, after one request with the system prompt,
    the page, the desk's tools and the model's settings"""
    model.says("Hello! How can I help?", usage=(950, 8))
    desk, agent = agent_for(model, "dmv")
    assert agent.reply("Hi") == "Hello! How can I help?"
    [request] = model.requests
    body = request.body
    assert body["model"] == MODEL and body["tools"] == tools() and body["max_tokens"] == 768
    assert all(body[key] == value for key, value in SAMPLING.items())
    system, user = body["messages"]
    assert system["content"].startswith(SYSTEM)
    assert system["content"].endswith("The caller opened the chat on the New York State's DMV pages.")
    assert user == {"role": "user", "content": "Hi"}
    [made] = agent.requests
    assert (made.prompt_tokens, made.completion_tokens, made.finish, made.calls) == (950, 8, "stop", ())
    assert made.seconds >= 0
    _, home = agent_for(model, None)
    assert home.messages[0]["content"].endswith("on the help desk's home page.")


@pytest.mark.id("tst_xtxxmd")
def test_the_tool_loop(model):
    """Each tool the model calls runs, and its result goes back with the model's message, until
    the model replies"""
    model.says(tool_calls=[("list_tickets", {})], usage=(900, 12))
    model.says("You have ticket T-2101.", usage=(1000, 9))
    desk, agent = agent_for(model)
    assert agent.reply("What tickets do I have?") == "You have ticket T-2101."
    second = model.requests[1].body["messages"]
    assert second[2]["role"] == "assistant"
    [call] = second[2]["tool_calls"]
    assert call["function"]["name"] == "list_tickets"
    assert second[3] == {
        "role": "tool",
        "tool_call_id": call["id"],
        "content": desk.call("list_tickets", "{}"),
    }
    assert [request.calls for request in agent.requests] == [("list_tickets",), ()]
    assert agent.requests[0] == Request(900, 12, agent.requests[0].seconds, "tool_calls", ("list_tickets",))


@pytest.mark.id("tst_16gu1a")
def test_calls_in_one_reply(model):
    """Calls the model makes together all run, in order, each result with its call's id"""
    model.says(
        tool_calls=[
            ("free_callbacks", {"service": "ssa", "day": "2026-11-03"}),
            ("list_tickets", {}),
        ]
    )
    model.says("Tuesday at 10:00 or 14:00.")
    _, agent = agent_for(model)
    agent.reply("When can someone call me?")
    calls = sent(model.requests[1], "assistant")[0]["tool_calls"]
    results = sent(model.requests[1], "tool")
    assert [result["tool_call_id"] for result in results] == [call["id"] for call in calls]
    assert json.loads(results[0]["content"]) == {"day": "2026-11-03", "free": ["10:00", "14:00"]}
    assert "tickets" in json.loads(results[1]["content"])


@pytest.mark.id("tst_ykq7em")
def test_a_conversation(model):
    """The conversation goes on from turn to turn, and each write is kept with the turn it came
    in"""
    model.says("I can book T-2101 on Tuesday at 10:00. Shall I?")
    model.says(tool_calls=[("book_callback", {"ticket": "T-2101", "day": "2026-11-03", "time": "10:00"})])
    model.says("Booked for Tuesday at 10:00.")
    desk, agent = agent_for(model)
    agent.reply("Can someone call me Tuesday at 10?")
    assert agent.reply("Yes, please book it.") == "Booked for Tuesday at 10:00."
    messages = model.requests[1].body["messages"]
    assert [message["role"] for message in messages] == ["system", "user", "assistant", "user"]
    assert messages[2]["content"] == "I can book T-2101 on Tuesday at 10:00. Shall I?"
    assert [write["turn"] for write in desk.writes] == [1]
    assert len(agent.messages) == 7


@pytest.mark.id("tst_irdt35")
def test_errors_go_back_to_the_model(model):
    """A call that can't run gives the model an error to read, and the turn goes on"""
    model.says(tool_calls=[("book_callback", '{"ticket": "T-2101", "day": ')])
    model.says(tool_calls=[("cancel_ticket", {"ticket": "T-2101"})])
    model.says("Sorry, I couldn't do that.")
    _, agent = agent_for(model)
    assert agent.reply("Book me in.") == "Sorry, I couldn't do that."
    results = [json.loads(sent(request, "tool")[-1]["content"]) for request in model.requests[1:]]
    assert all(list(result) == ["error"] for result in results)


@pytest.mark.id("tst_b46nyb")
def test_out_of_rounds(model):
    """A turn ends with OutOfRounds once the model still calls tools after rounds requests, and
    the next turn has rounds of its own"""
    for _ in range(3):
        model.says(tool_calls=[("list_tickets", {})])
    _, agent = agent_for(model, rounds=3)
    with pytest.raises(OutOfRounds):
        agent.reply("What tickets do I have?")
    assert len(model.requests) == 3
    model.says(tool_calls=[("list_tickets", {})])
    model.says(tool_calls=[("list_tickets", {})])
    model.says("T-2101 is open.")
    assert agent.reply("And now?") == "T-2101 is open."
    assert len(model.requests) == 6
