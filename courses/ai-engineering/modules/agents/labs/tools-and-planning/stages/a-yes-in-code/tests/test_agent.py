import numpy as np
import pytest

from actions import tools
from agent import MODEL, SAMPLING, SYSTEM, Agent, OutOfRounds, Request
from desk import Desk, Search

PASSAGES = [
    {
        "passage": "p1",
        "domain": "ssa",
        "title": "Get a Social Security card | SSA",
        "text": "Apply for a replacement card online or at an office.",
    },
]
FREE = {
    service: {"2026-11-03": ["10:00", "14:00"]}
    for service in ("ssa", "va", "studentaid", "dmv")
}
CARD = {
    "ticket": "T-2101",
    "service": "ssa",
    "status": "open",
    "summary": "Replacement card",
}


def agent_for(model, page="ssa", **options):
    model.embeds(lambda text: [1.0])
    desk = Desk(Search(model.client(), PASSAGES, np.array([[1]])), [CARD], FREE)
    return desk, Agent(model.client(), desk, page, **options)


def users(request):
    return [m["content"] for m in request.body["messages"] if m["role"] == "user"]


@pytest.mark.id("tst_rxawow")
def test_a_reply(model):
    """A reply with no tool calls comes back as it is, after one request with the system prompt,
    the page, the desk's reads and proposals, and the model's settings"""
    model.says("Hello! How can I help?", usage=(950, 8))
    _, agent = agent_for(model, "dmv")
    assert agent.reply("Hi") == "Hello! How can I help?"
    [request] = model.requests
    body = request.body
    assert body["model"] == MODEL and body["tools"] == tools()
    assert body["max_tokens"] == 768
    assert all(body[key] == value for key, value in SAMPLING.items())
    system = body["messages"][0]["content"]
    assert system.startswith(SYSTEM)
    assert system.endswith(
        "The caller opened the chat on the New York State's DMV pages."
    )
    [made] = agent.requests
    assert made == Request(950, 8, made.seconds, "stop", ())


@pytest.mark.id("tst_iclxu8")
def test_the_tool_loop(model):
    """Each tool the model calls runs, a read or a proposal, and its result goes back after the
    model's message with the call's id, until the model replies"""
    model.says(tool_calls=[("list_tickets", {})])
    model.says(
        tool_calls=[("propose_callback", {"service": "ssa", "day": "2026-11-03"})]
    )
    model.says("I can book T-2101 on Tuesday at 10:00. Shall I?")
    desk, agent = agent_for(model)
    assert (
        agent.reply("Call me Tuesday?")
        == "I can book T-2101 on Tuesday at 10:00. Shall I?"
    )
    messages = model.requests[2].body["messages"]
    assert [m["role"] for m in messages] == [
        "system",
        "user",
        "assistant",
        "tool",
        "assistant",
        "tool",
    ]
    assert messages[3]["content"].startswith("The caller's open tickets:")
    assert messages[5]["content"].startswith("Proposed: book a Social Security adviser")
    assert messages[5]["tool_call_id"] == messages[4]["tool_calls"][0]["id"]
    assert desk.writes == []


@pytest.mark.id("tst_jfn902")
def test_a_yes_in_code(model):
    """The caller's yes makes the proposal before the model reads it, and the message the model
    reads carries what the desk did"""
    model.says(
        tool_calls=[("propose_callback", {"service": "ssa", "day": "2026-11-03"})]
    )
    model.says("I can book T-2101 on Tuesday at 10:00. Shall I?")
    model.says("Booked: an adviser will call you on Tuesday at 10:00.")
    desk, agent = agent_for(model)
    agent.reply("Call me Tuesday?")
    assert agent.reply("Yes, please book it.") == (
        "Booked: an adviser will call you on Tuesday at 10:00."
    )
    assert [(w["tool"], w["time"], w["turn"]) for w in desk.writes] == [
        ("book_callback", "10:00", 1)
    ]
    assert users(model.requests[2])[-1] == (
        "Yes, please book it.\n\n(The desk: Done: an adviser will call the caller on "
        "Tuesday 2026-11-03 at 10:00 about T-2101.)"
    )


@pytest.mark.id("tst_aw5u8x")
def test_anything_else_drops_it(model):
    """A message that doesn't say yes drops the proposal and reaches the model as it was sent"""
    model.says(
        tool_calls=[("propose_callback", {"service": "ssa", "day": "2026-11-03"})]
    )
    model.says("I can book T-2101 on Tuesday at 10:00. Shall I?")
    model.says("Which time would suit you?")
    model.says("Nothing is booked.")
    desk, agent = agent_for(model)
    agent.reply("Call me Tuesday?")
    agent.reply("Is there anything later?")
    assert users(model.requests[2])[-1] == "Is there anything later?"
    assert agent.reply("Yes.") == "Nothing is booked."
    assert users(model.requests[3])[-1] == "Yes."
    assert desk.writes == []


@pytest.mark.id("tst_db1dcl")
def test_out_of_rounds(model):
    """A turn ends with OutOfRounds once the model still calls tools after rounds requests"""
    for _ in range(3):
        model.says(tool_calls=[("list_tickets", {})])
    _, agent = agent_for(model, rounds=3)
    with pytest.raises(OutOfRounds):
        agent.reply("What tickets do I have?")
    assert len(model.requests) == 3
