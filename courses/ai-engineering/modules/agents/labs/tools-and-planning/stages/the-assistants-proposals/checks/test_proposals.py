import numpy as np
import pytest

from desk import Desk, Search
from desk_actions import Actions

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
    service: {"2026-11-03": ["09:00", "10:00", "14:00"]}
    for service in ("ssa", "va", "studentaid", "dmv")
}


def actions_for(model, tickets=(CARD,)):
    model.embeds(lambda text: [1.0])
    desk = Desk(Search(model.client(), PASSAGES, np.array([[1]])), list(tickets), FREE)
    return desk, Actions(desk)


@pytest.mark.id("tst_p5bdze")
def test_nothing_before_the_yes(model):
    """A callback proposed on the caller's ticket books nothing until they say yes"""
    desk, actions = actions_for(model)
    actions.propose_callback("ssa", "2026-11-03", time="14:00")
    assert desk.writes == []
    assert "14:00" in desk.free["ssa"]["2026-11-03"]
    actions.heard("Yes, please book it.")
    assert [(write["tool"], write["time"]) for write in desk.writes] == [
        ("book_callback", "14:00")
    ]


@pytest.mark.id("tst_pv50zi")
def test_a_no_drops_it(model):
    """A message that doesn't say yes drops the proposal, so a later yes makes nothing"""
    desk, actions = actions_for(model)
    actions.propose_ticket("dmv", "My new license hasn't come.")
    assert actions.heard("No, thanks.") is None
    assert actions.heard("Yes.") is None
    assert desk.writes == []


@pytest.mark.id("tst_v71m4o")
def test_a_yes_to_a_time_taken_since(model):
    """A yes to a time taken since it was proposed makes nothing and says why"""
    desk, actions = actions_for(model)
    actions.propose_callback("va", "2026-11-03", time="10:00", summary="My pension")
    desk.free["va"]["2026-11-03"].remove("10:00")
    said = actions.heard("Yes, please.")
    assert isinstance(said, str) and said.startswith("The desk couldn't do it")
    assert desk.writes == [] and desk.tickets == [CARD]


@pytest.mark.id("tst_khtbi4")
def test_two_open_tickets(model):
    """With two open tickets for the service, the desk asks which the call is about"""
    desk, actions = actions_for(model, (CARD, CLAIM))
    said = actions.call("propose_callback", '{"service": "ssa", "day": "2026-11-03"}')
    assert said.startswith("Error: The caller has 2 open Social Security tickets")
    assert actions.pending is None and desk.writes == []
