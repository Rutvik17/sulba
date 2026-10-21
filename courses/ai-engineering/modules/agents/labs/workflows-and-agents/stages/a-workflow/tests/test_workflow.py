import json

import numpy as np
import pytest

from desk import Desk, Search
from workflow import MODEL, ROUTE, SAMPLING, Route, Workflow, route

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
]
VECTORS = np.array([[1, 0], [0, 1]])
FREE = {
    service: {"2026-11-03": ["10:00", "14:00", "15:00"]}
    for service in ("ssa", "va", "studentaid", "dmv")
}
CARD = {"ticket": "T-2101", "service": "ssa", "status": "open", "summary": "Replacement card"}
GI_BILL = {"ticket": "T-1901", "service": "va", "status": "open", "summary": "GI Bill payment"}


def routed(kind, service="none", day="none", time="none", part="none"):
    return json.dumps({"kind": kind, "service": service, "day": day, "time": time, "part": part})


def desk_for(model, tickets=()):
    model.embeds(lambda text: [1.0, 0.0])
    return Desk(Search(model.client(), PASSAGES, VECTORS), list(tickets), FREE)


@pytest.mark.id("tst_dcuvt8")
def test_route(model):
    """A message is sorted by one request whose reply follows the route's schema, with the page
    the chat was opened from, and none read as None"""
    model.says(routed("callback", "va", "2026-11-03", "none", "morning"))
    found = route(model.client(), "Can someone call me Tuesday morning?", "va")
    assert found == Route("callback", "va", "2026-11-03", None, "morning")
    [request] = model.requests
    assert request.body["model"] == MODEL
    assert request.body["response_format"] == {
        "type": "json_schema",
        "json_schema": {"schema": ROUTE},
    }
    assert all(request.body[key] == value for key, value in SAMPLING.items())
    system, user = request.body["messages"]
    assert system["role"] == "system" and "veterans' benefits pages" in system["content"]
    assert user == {"role": "user", "content": "Can someone call me Tuesday morning?"}


@pytest.mark.id("tst_x2xcot")
def test_route_fills_the_page(model):
    """A service the message doesn't name is the page's, and a reply that isn't a route, or
    sorts the message as something else, is the route other"""
    model.says(routed("question"))
    assert route(model.client(), "What do I bring?", "dmv") == Route("question", "dmv")
    model.says(routed("question"))
    assert route(model.client(), "What do I bring?", None) == Route("question")
    model.says("I think it's a question.")
    assert route(model.client(), "What do I bring?", "dmv") == Route("other")
    model.says(routed("greeting"))
    assert route(model.client(), "Hi!", "dmv") == Route("other")
    model.says('{"kind": "case"}')
    assert route(model.client(), "Hi!", "dmv") == Route("other")


@pytest.mark.id("tst_3a9nlr")
def test_question(model):
    """A question is answered by a second request, from the passages the search finds for it in
    the service's pages"""
    desk = desk_for(model)
    model.says(routed("question", "ssa"))
    model.says("Apply online [p1].")
    workflow = Workflow(model.client(), desk, "ssa")
    assert workflow.reply("How do I replace my card?") == "Apply online [p1]."
    embedding, answer = model.requests[1:]
    assert embedding.body["input"] == "search_query: How do I replace my card?"
    content = answer.body["messages"][1]["content"]
    assert "[p1] Get a Social Security card" in content
    assert "[p2]" not in content
    assert "How do I replace my card?" in content
    assert desk.writes == []


@pytest.mark.id("tst_ww07em")
def test_case_waits_for_yes(model):
    """A case opens a ticket for its service only once the caller says yes, with their message
    as its summary"""
    desk = desk_for(model)
    model.says(routed("case", "dmv"))
    workflow = Workflow(model.client(), desk, "dmv")
    case = "My new license hasn't come."
    offer = workflow.reply(case)
    assert offer.endswith("?") and desk.writes == []
    done = workflow.reply("Yes, please open the ticket.")
    assert desk.writes == [{"tool": "open_ticket", "ticket": "T-3001", "service": "dmv", "turn": 1}]
    assert desk.tickets[-1]["summary"] == case
    assert "T-3001" in done
    assert len(model.requests) == 1


@pytest.mark.id("tst_9pn4w0")
def test_a_no_changes_nothing(model):
    """Anything but a yes drops the offer and is sorted as a new message"""
    desk = desk_for(model)
    model.says(routed("case", "dmv"))
    model.says(routed("other"))
    model.says(routed("other"))
    workflow = Workflow(model.client(), desk, "dmv")
    workflow.reply("My new license hasn't come.")
    workflow.reply("No, leave it for now.")
    assert workflow.reply("Yes.") and desk.writes == []
    assert len(model.requests) == 3


@pytest.mark.id("tst_y78ruw")
def test_callback(model):
    """A callback is offered on the caller's open ticket for the service, at the time asked, or
    the first free time in the part of the day asked, and booked once they say yes"""
    desk = desk_for(model, [CARD, GI_BILL])
    model.says(routed("callback", "ssa", "2026-11-03", "14:00"))
    workflow = Workflow(model.client(), desk, "ssa")
    offer = workflow.reply("Can someone call me Tuesday at 14:00?")
    assert "T-2101" in offer and "14:00" in offer and desk.writes == []
    done = workflow.reply("Yes, please book it.")
    assert desk.writes == [
        {"tool": "book_callback", "ticket": "T-2101", "day": "2026-11-03", "time": "14:00", "turn": 1}
    ]
    assert "14:00" in done
    desk = desk_for(model, [CARD, GI_BILL])
    model.says(routed("callback", "va", "2026-11-03", "none", "afternoon"))
    workflow = Workflow(model.client(), desk, None)
    assert "14:00" in workflow.reply("Can someone call me Tuesday afternoon about my GI Bill?")
    workflow.reply("Yes, please go ahead.")
    assert [write["time"] for write in desk.writes] == ["14:00"]


@pytest.mark.id("tst_bmfk9c")
def test_callback_with_a_new_ticket(model):
    """A callback for a service the caller has no open ticket for opens one and books it, once
    they say yes"""
    desk = desk_for(model, [GI_BILL])
    model.says(routed("callback", "dmv", "2026-11-03", "none", "morning"))
    workflow = Workflow(model.client(), desk, "dmv")
    workflow.reply("Can an adviser call me Tuesday morning about my road test?")
    assert desk.writes == []
    workflow.reply("Yes, please open it and book the call.")
    assert desk.writes == [
        {"tool": "open_ticket", "ticket": "T-3001", "service": "dmv", "turn": 1},
        {"tool": "book_callback", "ticket": "T-3001", "day": "2026-11-03", "time": "10:00", "turn": 1},
    ]


@pytest.mark.id("tst_lww1a8")
def test_asks_when_it_cant_tell(model):
    """A callback the desk can't place, or a message it can't sort, is answered with a question
    about the caller's open tickets, and changes nothing"""
    second = {"ticket": "T-2102", "service": "ssa", "status": "open", "summary": "Disability claim"}
    desk = desk_for(model, [CARD, second, GI_BILL])
    model.says(routed("callback", "ssa", "2026-11-03", "none", "morning"))
    model.says(routed("other"))
    model.says(routed("callback", "none", "2026-11-03"))
    workflow = Workflow(model.client(), desk, "ssa")
    for message in ["Call me Tuesday morning.", "Yes, please.", "Hello?"]:
        reply = workflow.reply(message)
        assert reply.endswith("?") or "?" in reply
        assert "T-2101" in reply and "T-1901" in reply
    assert desk.writes == []


@pytest.mark.id("tst_i7ruhp")
def test_callback_at_a_time_taken(model):
    """A time the advisers aren't free is answered with the times they are, and nothing waits
    for a yes"""
    desk = desk_for(model, [CARD])
    model.says(routed("callback", "ssa", "2026-11-03", "09:00"))
    model.says(routed("other"))
    workflow = Workflow(model.client(), desk, "ssa")
    reply = workflow.reply("Can someone call me Tuesday at 9?")
    assert "10:00, 14:00, 15:00" in reply
    workflow.reply("Yes, please.")
    assert desk.writes == []
