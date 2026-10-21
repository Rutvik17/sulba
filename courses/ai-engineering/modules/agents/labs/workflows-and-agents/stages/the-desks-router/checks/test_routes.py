import json

import numpy as np
import pytest

from desk import Desk, Search
from router import Router

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
CLAIM = {"ticket": "T-2102", "service": "ssa", "status": "open", "summary": "Disability claim"}


def routed(kind, service="none", day="none", time="none", part="none"):
    return json.dumps({"kind": kind, "service": service, "day": day, "time": time, "part": part})


def router_for(model, page, tickets=(CARD,)):
    model.embeds(lambda text: [1.0])
    desk = Desk(Search(model.client(), PASSAGES, np.array([[1]])), list(tickets), FREE)
    return desk, Router(model.client(), desk, page)


def chats(model):
    return [request.body for request in model.requests if "messages" in request.body]


@pytest.mark.id("tst_2o51bb")
def test_sorted_once(model):
    """A conversation is sorted once, by its first message, down either path"""
    model.says(routed("callback", "ssa", "2026-11-03", "10:00"))
    desk, router = router_for(model, "ssa")
    router.reply("Can someone call me Tuesday at 10?")
    router.reply("Yes, please book it.")
    assert [write["time"] for write in desk.writes] == ["10:00"]
    model.says(routed("other"))
    model.says("How can I help?")
    model.says("I can help with that.")
    _, router = router_for(model, "ssa")
    router.reply("Hello")
    router.reply("I'd like to know about my card.")
    sorted_ = [body for body in chats(model) if "response_format" in body]
    assert len(sorted_) == 2


@pytest.mark.id("tst_ecn8ol")
def test_two_tickets_go_to_the_agent(model):
    """A callback for a service with two open tickets goes to the agent"""
    model.says(routed("callback", "ssa", "2026-11-03", "none", "morning"))
    model.says("Is it about T-2101 or T-2102?")
    desk, router = router_for(model, "ssa", (CARD, CLAIM))
    assert router.reply("Can someone call me Tuesday morning?") == "Is it about T-2101 or T-2102?"
    assert "tools" in chats(model)[1]
    assert desk.writes == []


@pytest.mark.id("tst_ganb87")
def test_the_rest_go_to_the_agent(model):
    """A message sorted as other, or a callback with no day, goes to the agent"""
    for found in [routed("other"), routed("callback", "ssa")]:
        model.requests.clear()
        model.says(found)
        model.says("When would suit you?")
        _, router = router_for(model, "ssa")
        assert router.reply("Can someone ring me?") == "When would suit you?"
        assert "tools" in chats(model)[1]
