import json

import numpy as np
import pytest

from actions import ACTIONS, Actions, tools
from desk import TOOLS, Desk, Search

PASSAGES = [
    {
        "passage": "p1",
        "domain": "ssa",
        "title": "Get a Social Security card | SSA",
        "text": "Apply for a replacement card online or at an office.",
    },
]
CARD = {
    "ticket": "T-2101",
    "service": "ssa",
    "status": "open",
    "summary": "Replacement card",
}
CLAIM = {
    "ticket": "T-2102",
    "service": "ssa",
    "status": "open",
    "summary": "Disability claim",
}
FREE = {
    service: {"2026-11-03": ["09:00", "10:00", "14:00"], "2026-11-04": []}
    for service in ("ssa", "va", "studentaid", "dmv")
}


def actions_for(model, tickets=(CARD,)):
    model.embeds(lambda text: [1.0])
    desk = Desk(Search(model.client(), PASSAGES, np.array([[1]])), list(tickets), FREE)
    return desk, Actions(desk)


@pytest.mark.id("tst_6wa2qr")
def test_a_ticket_waits_for_a_yes(model):
    """A proposed ticket changes nothing until the caller's next message says yes"""
    desk, actions = actions_for(model)
    said = actions.propose_ticket("dmv", "My new license hasn't come.")
    assert said == (
        "Proposed: open a ticket for a New York State's DMV adviser to look into this: My "
        "new license hasn't come. Ask the caller whether to go ahead. The desk does it when "
        "they say yes."
    )
    assert desk.writes == []
    desk.turn = 1
    assert actions.heard("Yes, please open the ticket.") == (
        "Done: ticket T-3001 is open for an adviser."
    )
    assert [(write["tool"], write["turn"]) for write in desk.writes] == [
        ("open_ticket", 1)
    ]


@pytest.mark.id("tst_qcsntn")
def test_anything_but_a_yes_drops_it(model):
    """A message that doesn't say yes drops the proposal, and a later yes makes nothing"""
    desk, actions = actions_for(model)
    actions.propose_ticket("dmv", "My new license hasn't come.")
    assert actions.heard("Actually, what does it cost?") is None
    assert actions.pending is None
    assert actions.heard("Yes.") is None
    assert actions.confirm() == "Nothing was waiting for the caller's yes."
    assert desk.writes == []


@pytest.mark.id("tst_9oiq60")
def test_a_callback_on_the_callers_ticket(model):
    """A callback is proposed on the caller's open ticket for the service, at the hour asked or
    the first free one in the part of the day asked"""
    desk, actions = actions_for(model)
    said = actions.propose_callback("ssa", "2026-11-03", time="14:00")
    assert said.startswith(
        "Proposed: book a Social Security adviser to call the caller on Tuesday 2026-11-03 "
        "at 14:00 about T-2101, Replacement card."
    )
    actions.propose_callback("ssa", "2026-11-03", part="morning")
    assert actions.heard("Yes, please book it.") == (
        "Done: an adviser will call the caller on Tuesday 2026-11-03 at 09:00 about T-2101."
    )
    assert desk.free["ssa"]["2026-11-03"] == ["10:00", "14:00"]
    assert [write["time"] for write in desk.writes] == ["09:00"]


@pytest.mark.id("tst_h7a6xz")
def test_a_callback_on_a_new_ticket(model):
    """With no open ticket for the service, a callback is proposed with a new ticket, which the
    yes opens before it books the call"""
    desk, actions = actions_for(model)
    actions.propose_callback(
        "va", "2026-11-03", part="afternoon", summary="My pension application"
    )
    assert actions.heard("Yes, please open it and book the call.") == (
        "Done: an adviser will call the caller on Tuesday 2026-11-03 at 14:00 about T-3001."
    )
    assert [(write["tool"], write["ticket"]) for write in desk.writes] == [
        ("open_ticket", "T-3001"),
        ("book_callback", "T-3001"),
    ]


@pytest.mark.id("tst_9744x8")
def test_what_the_desk_looks_up_first(model):
    """A callback the desk can't make is refused before the caller is asked, with what to do
    instead"""
    desk, actions = actions_for(model, (CARD, CLAIM))
    with pytest.raises(Exception, match=r"2 open Social Security tickets: T-2101"):
        actions.propose_callback("ssa", "2026-11-03")
    with pytest.raises(Exception, match=r"no open Social Security ticket T-9999"):
        actions.propose_callback("ssa", "2026-11-03", ticket="T-9999")
    with pytest.raises(Exception, match=r"Call again with summary"):
        actions.propose_callback("dmv", "2026-11-03")
    with pytest.raises(
        Exception, match=r"aren't free at 11:00 on Tuesday 2026-11-03. They're free at "
    ):
        actions.propose_callback("ssa", "2026-11-03", time="11:00", ticket="T-2102")
    with pytest.raises(Exception, match=r"aren't free on Wednesday 2026-11-04\.$"):
        actions.propose_callback("ssa", "2026-11-04", ticket="T-2102")
    assert actions.pending is None and desk.writes == []


@pytest.mark.id("tst_0pcrij")
def test_a_yes_checks_again(model):
    """A yes to a time taken since it was proposed books nothing and says why"""
    desk, actions = actions_for(model)
    actions.propose_callback("ssa", "2026-11-03", time="10:00")
    desk.free["ssa"]["2026-11-03"].remove("10:00")
    assert actions.heard("Yes.").startswith("The desk couldn't do it: ")
    assert desk.writes == []


@pytest.mark.id("tst_qqzvle")
def test_calls(model):
    """call runs the desk's reads and the proposals, and each error says how to call again"""
    desk, actions = actions_for(model, (CARD, CLAIM))
    assert [each["function"]["name"] for each in tools()] == [*TOOLS, *ACTIONS]
    assert actions.call("list_tickets", "{}") == desk.list_tickets()
    said = actions.call(
        "propose_callback",
        json.dumps({"service": "ssa", "day": "2026-11-03", "ticket": "T-2102"}),
    )
    assert said.startswith("Proposed: book a Social Security adviser")
    assert actions.call("propose_callback", '{"service": "ssa"}').startswith(
        "Error: propose_callback needs day, the date, Monday 2026-11-02 to Friday "
        "2026-11-06. For example: "
    )
    assert actions.call(
        "propose_callback", '{"service": "ssa", "day": "2026-11-03"}'
    ).startswith("Error: The caller has 2 open Social Security tickets")
    assert actions.call("book_callback", "{}").startswith(
        "Error: there is no tool named 'book_callback'."
    )
    assert desk.writes == []
