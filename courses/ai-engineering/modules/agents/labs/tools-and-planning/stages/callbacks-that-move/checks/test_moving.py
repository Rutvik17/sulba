import numpy as np
import pytest

from desk import Desk, Search
from moves import Moves

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
FREE = {
    service: {
        "2026-11-03": ["09:00", "14:00"],
        "2026-11-05": ["10:00", "13:00", "15:00"],
    }
    for service in ("ssa", "va", "studentaid", "dmv")
}
BOOKED = {"ticket": "T-2101", "day": "2026-11-03", "time": "10:00"}


def moves_for(model, callbacks=(BOOKED,)):
    model.embeds(lambda text: [1.0])
    search = Search(model.client(), PASSAGES, np.array([[1]]))
    desk = Desk(search, [CARD], FREE, list(callbacks))
    return desk, Moves(desk)


@pytest.mark.id("tst_e89lep")
def test_only_on_a_yes(model):
    """A move changes nothing until the caller says yes, and anything else drops it"""
    desk, moves = moves_for(model)
    moves.propose_move("T-2101", "2026-11-05", time="15:00")
    assert desk.callbacks == [BOOKED] and desk.writes == []
    assert moves.heard("Hmm, let me think.") is None
    assert moves.heard("Yes.") is None
    assert desk.callbacks == [BOOKED] and desk.writes == []


@pytest.mark.id("tst_3ovmgf")
def test_never_without_a_call(model):
    """The new time is booked before the old one is freed, and the old one is free again after"""
    desk, moves = moves_for(model)
    moves.propose_move("T-2101", "2026-11-05", time="15:00")
    moves.heard("Yes, please.")
    assert [write["tool"] for write in desk.writes] == [
        "book_callback",
        "cancel_callback",
    ]
    assert "10:00" in desk.free["ssa"]["2026-11-03"]
    assert "15:00" not in desk.free["ssa"]["2026-11-05"]


@pytest.mark.id("tst_simqzc")
def test_the_old_call_stays(model):
    """When the new time has gone by the caller's yes, the call stays where it was and the desk
    says the times that are free"""
    desk, moves = moves_for(model)
    moves.propose_move("T-2101", "2026-11-05", time="15:00")
    desk.free["ssa"]["2026-11-05"].remove("15:00")
    said = moves.heard("Yes.")
    assert said is not None and "10:00, 13:00" in said
    assert desk.callbacks == [BOOKED] and desk.writes == []


@pytest.mark.id("tst_28zuzw")
def test_a_call_they_have(model):
    """A move of a call the caller hasn't booked is refused with the calls they have, and a time
    that isn't free with the times that are"""
    _, moves = moves_for(model)
    said = moves.call("propose_move", '{"ticket": "T-2109", "day": "2026-11-05"}')
    assert said.startswith("Error: ") and "Tuesday 2026-11-03 at 10:00: T-2101" in said
    said = moves.call(
        "propose_move", '{"ticket": "T-2101", "day": "2026-11-05", "time": "09:00"}'
    )
    assert said.startswith("Error: ") and "10:00, 13:00, 15:00" in said
    assert moves.pending is None
