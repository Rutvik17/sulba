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


@pytest.mark.id("tst_cbr0ty")
def test_a_ticket(model):
    """A proposed ticket is opened once the caller says yes"""
    desk, actions = actions_for(model)
    actions.propose_ticket("dmv", "My new license hasn't come.")
    assert actions.heard("Yes, please open the ticket.").startswith("Done")
    assert [write["tool"] for write in desk.writes] == ["open_ticket"]


@pytest.mark.id("tst_647qfi")
def test_a_callback(model):
    """A callback on the caller's ticket is booked at the time asked once they say yes"""
    desk, actions = actions_for(model)
    actions.propose_callback("ssa", "2026-11-03", time="14:00")
    assert actions.heard("Yes, please book it.").startswith("Done")
    assert [(write["ticket"], write["time"]) for write in desk.writes] == [
        ("T-2101", "14:00")
    ]


@pytest.mark.id("tst_0gc8p9")
def test_a_callback_on_a_new_ticket(model):
    """A callback for a service the caller has no ticket for opens one and books on it"""
    desk, actions = actions_for(model)
    actions.propose_callback("va", "2026-11-03", part="morning", summary="My pension")
    assert actions.heard("Yes.").startswith("Done")
    assert [write["tool"] for write in desk.writes] == ["open_ticket", "book_callback"]
