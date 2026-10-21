import json

import numpy as np
import pytest

from desk import Desk, Search

PASSAGES = [
    {
        "passage": "p1",
        "domain": "ssa",
        "title": "Get a Social Security card | SSA",
        "text": "Apply for a replacement card online or at an office.",
    },
    {
        "passage": "p2",
        "domain": "dmv",
        "title": "Renew a license | DMV",
        "text": "Renew your driver license online before it expires.",
    },
    {
        "passage": "p3",
        "domain": "ssa",
        "title": "Report a change of address | SSA",
        "text": "Report your new address online so letters reach you.",
    },
]
VECTORS = np.array([[1, 0, 0], [0, 1, 0], [0.6, 0, 0.8]])
TICKETS = [
    {
        "ticket": "T-2101",
        "service": "ssa",
        "status": "open",
        "summary": "Replacement card",
    },
    {
        "ticket": "T-1901",
        "service": "va",
        "status": "closed",
        "summary": "GI Bill payment",
    },
]
FREE = {
    service: {day: ["10:00", "14:00"] for day in ("2026-11-02", "2026-11-03")}
    for service in ("ssa", "va", "studentaid", "dmv")
}


def desk_for(model):
    model.embeds(lambda text: [1.0, 0.0, 0.0] if "card" in text else [0.0, 1.0, 0.0])
    return Desk(Search(model.client(), PASSAGES, VECTORS), TICKETS, FREE)


@pytest.mark.id("tst_oz00nn")
def test_list_tickets(model):
    """The caller's tickets, as copies the caller of the tool can't change the desk through"""
    desk = desk_for(model)
    found = desk.list_tickets()
    assert found == {"tickets": TICKETS}
    found["tickets"][0]["status"] = "closed"
    assert desk.list_tickets()["tickets"][0]["status"] == "open"


@pytest.mark.id("tst_8kix40")
def test_open_ticket(model):
    """A ticket opened gets the next id from T-3001, and the write is kept with its turn"""
    desk = desk_for(model)
    assert desk.open_ticket("dmv", "The new license hasn't come.") == {
        "ticket": "T-3001"
    }
    desk.turn = 1
    assert desk.open_ticket("ssa", "The card hasn't come.") == {"ticket": "T-3002"}
    assert desk.list_tickets()["tickets"][-1] == {
        "ticket": "T-3002",
        "service": "ssa",
        "status": "open",
        "summary": "The card hasn't come.",
    }
    assert desk.writes == [
        {"tool": "open_ticket", "ticket": "T-3001", "service": "dmv", "turn": 0},
        {"tool": "open_ticket", "ticket": "T-3002", "service": "ssa", "turn": 1},
    ]
    assert "error" in desk.open_ticket("irs", "A tax question.")
    assert "error" in desk.open_ticket("ssa", "  ")
    assert len(desk.writes) == 2


@pytest.mark.id("tst_07n9lk")
def test_free_callbacks(model):
    """The free times of a service's advisers on a day, or an error for a service or day the
    desk doesn't have"""
    desk = desk_for(model)
    assert desk.free_callbacks("va", "2026-11-03") == {
        "day": "2026-11-03",
        "free": ["10:00", "14:00"],
    }
    assert "error" in desk.free_callbacks("irs", "2026-11-03")
    assert "error" in desk.free_callbacks("va", "Tuesday")


@pytest.mark.id("tst_mrxz6v")
def test_book_callback(model):
    """A callback booked on an open ticket at a free time takes that time, and anything else is
    an error that books nothing"""
    desk = desk_for(model)
    desk.turn = 1
    booked = desk.book_callback("T-2101", "2026-11-02", "14:00")
    assert booked == {
        "booked": {"ticket": "T-2101", "day": "2026-11-02", "time": "14:00"}
    }
    assert desk.free_callbacks("ssa", "2026-11-02")["free"] == ["10:00"]
    assert desk.free_callbacks("va", "2026-11-02")["free"] == ["10:00", "14:00"]
    assert desk.writes == [
        {
            "tool": "book_callback",
            "ticket": "T-2101",
            "day": "2026-11-02",
            "time": "14:00",
            "turn": 1,
        }
    ]
    for wrong in [
        ("T-2101", "2026-11-02", "14:00"),
        ("T-2101", "2026-11-02", "09:00"),
        ("T-2101", "2026-11-09", "10:00"),
        ("T-1901", "2026-11-02", "10:00"),
        ("T-9999", "2026-11-02", "10:00"),
    ]:
        assert "error" in desk.book_callback(*wrong)
    assert len(desk.writes) == 1


@pytest.mark.id("tst_34hzhb")
def test_search_help(model):
    """Search gives the passages the fused search finds, of every page or of one service's"""
    desk = desk_for(model)
    found = desk.search_help("replacement card address")["results"]
    assert [each["passage"] for each in found] == ["p1", "p3", "p2"]
    assert found[0] == {
        "passage": "p1",
        "page": "Get a Social Security card",
        "text": "Apply for a replacement card online or at an office.",
    }
    found = desk.search_help("renew online", "dmv")["results"]
    assert [each["passage"] for each in found] == ["p2"]
    assert "error" in desk.search_help("renew", "irs")
    assert model.requests[0].body["input"] == "search_query: replacement card address"


@pytest.mark.id("tst_op5jcn")
def test_call(model):
    """A model's call runs its tool with its arguments and gives the result as JSON text"""
    desk = desk_for(model)
    result = desk.call("free_callbacks", '{"service": "dmv", "day": "2026-11-02"}')
    assert json.loads(result) == {"day": "2026-11-02", "free": ["10:00", "14:00"]}
    assert json.loads(desk.call("list_tickets", "{}")) == {"tickets": TICKETS}
    assert json.loads(desk.call("list_tickets", "")) == {"tickets": TICKETS}


@pytest.mark.id("tst_vrmub7")
def test_call_that_cant_run(model):
    """A call that can't run gives an error as JSON text instead of raising, and changes
    nothing"""
    desk = desk_for(model)
    for name, arguments in [
        ("cancel_ticket", '{"ticket": "T-2101"}'),
        ("open_ticket", '{"service": "ssa", "summary": '),
        ("open_ticket", '["ssa", "The card"]'),
        ("open_ticket", '{"service": "ssa"}'),
        ("open_ticket", '{"service": "ssa", "summary": "The card", "urgent": "yes"}'),
        ("book_callback", '{"ticket": "T-2101", "day": "2026-11-02", "time": 14}'),
    ]:
        result = json.loads(desk.call(name, arguments))
        assert list(result) == ["error"], (name, arguments)
        assert isinstance(result["error"], str)
    assert desk.writes == []
