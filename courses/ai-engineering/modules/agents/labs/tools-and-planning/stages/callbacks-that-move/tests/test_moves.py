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


@pytest.mark.id("tst_e7hf43")
def test_list_callbacks(model):
    """The caller's booked callbacks, each with its day, time, ticket, service and summary"""
    _, moves = moves_for(model)
    assert moves.list_callbacks() == (
        "The caller's booked callbacks:\n"
        "Tuesday 2026-11-03 at 10:00: T-2101, Social Security, Replacement card"
    )
    _, none = moves_for(model, ())
    assert none.list_callbacks() == "The caller has no callbacks booked."


@pytest.mark.id("tst_ni2o23")
def test_a_move(model):
    """A move proposed to the first free time in the part of the day asked is made on a yes"""
    desk, moves = moves_for(model)
    said = moves.propose_move("T-2101", "2026-11-05", part="afternoon")
    assert said.startswith(
        "Proposed: move the call about T-2101 from Tuesday 2026-11-03 at 10:00 to Thursday "
        "2026-11-05 at 13:00."
    )
    assert moves.heard("Yes, please move it.") == (
        "Done: the call about T-2101 is now on Thursday 2026-11-05 at 13:00."
    )
    assert desk.callbacks == [
        {"ticket": "T-2101", "day": "2026-11-05", "time": "13:00"}
    ]


@pytest.mark.id("tst_f5e1zv")
def test_calls(model):
    """call runs the moves' tools as it runs the others"""
    _, moves = moves_for(model)
    assert moves.call("list_callbacks", "{}") == moves.list_callbacks()
    assert moves.call(
        "propose_move", '{"ticket": "T-2101", "day": "2026-11-05", "time": "15:00"}'
    ).startswith("Proposed: move the call about T-2101")
    assert moves.call("propose_move", '{"ticket": "T-2101"}').startswith(
        "Error: propose_move needs day"
    )
