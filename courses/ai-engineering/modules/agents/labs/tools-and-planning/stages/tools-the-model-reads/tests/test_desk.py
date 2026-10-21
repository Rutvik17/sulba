import json

import numpy as np
import pytest

from desk import EXAMPLES, TOOLS, Desk, Search, tools

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


def desk_for(model, tickets=TICKETS):
    model.embeds(lambda text: [1.0, 0.0, 0.0] if "card" in text else [0.0, 1.0, 0.0])
    return Desk(Search(model.client(), PASSAGES, VECTORS), tickets, FREE)


@pytest.mark.id("tst_qaw0e1")
def test_search_help(model):
    """The passages found, best first, each led by its id in square brackets and its page's title,
    after a line that says where they're from and how to cite them"""
    desk = desk_for(model)
    found = desk.search_help("replacement card address", "ssa")
    assert found == (
        "2 passages from the Social Security pages, best first. Cite each one you use by its "
        "id in square brackets, like [p1].\n\n"
        "[p1] Get a Social Security card\n"
        "Apply for a replacement card online or at an office.\n\n"
        "[p3] Report a change of address\n"
        "Report your new address online so letters reach you."
    )
    everywhere = desk.search_help("renew license")
    assert everywhere.startswith("3 passages from every service's pages, best first.")
    assert everywhere.index("[p2]") < everywhere.index("[p1]")


@pytest.mark.id("tst_0b1joc")
def test_list_tickets(model):
    """The caller's tickets with a status, open by default, and how many have the other"""
    desk = desk_for(model)
    assert desk.list_tickets() == (
        "The caller's open tickets:\n"
        "T-2101: Social Security, Replacement card\n"
        'They have 1 closed ticket: list_tickets with status "closed" lists them.'
    )
    assert desk.list_tickets("closed") == (
        "The caller's closed tickets:\n"
        "T-1901: veterans' benefits, GI Bill payment\n"
        'They have 1 open ticket: list_tickets with status "open" lists them.'
    )
    assert desk_for(model, []).list_tickets() == "The caller has no open tickets."


@pytest.mark.id("tst_yrz6uv")
def test_a_call(model):
    """call runs the tool with the arguments the model wrote, and gives its result"""
    desk = desk_for(model)
    assert desk.call("list_tickets", '{"status": "closed"}') == desk.list_tickets(
        "closed"
    )
    assert desk.call("list_tickets", "") == desk.list_tickets()
    assert desk.call(
        "search_help", json.dumps({"query": "card", "service": "ssa"})
    ) == desk.search_help("card", "ssa")


@pytest.mark.id("tst_uwuh0b")
def test_errors_that_say_how_to_call_again(model):
    """A call that can't run gives an error that names what's wrong and what to send instead,
    and changes nothing"""
    desk = desk_for(model)
    example = json.dumps(EXAMPLES["search_help"])
    assert desk.call("open_ticket", "{}") == (
        "Error: there is no tool named 'open_ticket'. The tools are search_help, "
        "list_tickets."
    )
    assert desk.call("search_help", '{"query": "card", ') == (
        f"Error: search_help's arguments are one JSON object, like {example}, and these "
        "aren't."
    )
    assert desk.call("search_help", '["card"]').startswith(
        "Error: search_help's arguments are one JSON object"
    )
    assert desk.call("search_help", '{"service": "ssa"}') == (
        "Error: search_help needs query, what to search for, in the caller's words. For "
        f"example: {example}"
    )
    assert desk.call("search_help", '{"query": "card", "page": 2}') == (
        f"Error: search_help takes no page. It takes query, service, like {example}"
    )
    assert desk.call("search_help", '{"query": "card", "service": "SSA"}') == (
        'Error: service is ssa, va, studentaid, dmv, not "SSA".'
    )
    assert desk.call("list_tickets", '{"status": 1}') == (
        "Error: status is open, closed, not 1."
    )
    assert desk.call("search_help", '{"query": 5}') == (
        "Error: query is a string, not 5."
    )
    assert desk.writes == []


@pytest.mark.id("tst_e60xf5")
def test_writes(model):
    """The desk opens tickets and books and cancels callbacks itself, keeping each with its turn,
    and an error says why one can't be made"""
    desk = desk_for(model)
    desk.turn = 1
    assert desk.open_ticket("dmv", "License not arrived") == "T-3001"
    desk.book_callback("T-3001", "2026-11-03", "14:00")
    assert desk.free["dmv"]["2026-11-03"] == ["10:00"]
    assert [write["tool"] for write in desk.writes] == ["open_ticket", "book_callback"]
    assert {write["turn"] for write in desk.writes} == {1}
    assert desk.callbacks == [{"ticket": "T-3001", "day": "2026-11-03", "time": "14:00"}]
    with pytest.raises(Exception, match="free at 10:00"):
        desk.book_callback("T-3001", "2026-11-03", "14:00")
    with pytest.raises(Exception, match="no open ticket T-1901"):
        desk.book_callback("T-1901", "2026-11-03", "10:00")
    desk.cancel_callback("T-3001", "2026-11-03", "14:00")
    assert desk.callbacks == []
    assert desk.free["dmv"]["2026-11-03"] == ["10:00", "14:00"]
    assert desk.writes[-1]["tool"] == "cancel_callback"
    with pytest.raises(Exception, match="no callback about T-3001"):
        desk.cancel_callback("T-3001", "2026-11-03", "14:00")


@pytest.mark.id("tst_8uztz0")
def test_tools():
    """The desk's tools as a chat request gives them, each with an example call that fits"""
    assert [each["function"]["name"] for each in tools()] == list(TOOLS)
    for name, tool in TOOLS.items():
        properties = tool["parameters"]["properties"]
        assert all(
            "description" in each and each["description"].endswith(".")
            for each in properties.values()
        )
        assert set(EXAMPLES[name]) <= set(properties)
