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
GI_BILL = {"ticket": "T-1901", "service": "va", "status": "open", "summary": "GI Bill payment"}


def routed(kind, service="none", day="none", time="none", part="none"):
    return json.dumps({"kind": kind, "service": service, "day": day, "time": time, "part": part})


def router_for(model, page, tickets=(CARD, GI_BILL)):
    model.embeds(lambda text: [1.0])
    desk = Desk(Search(model.client(), PASSAGES, np.array([[1]])), list(tickets), FREE)
    return desk, Router(model.client(), desk, page)


def with_tools(model):
    return ["tools" in request.body for request in model.requests if "messages" in request.body]


@pytest.mark.id("tst_h0f54q")
def test_a_question(model):
    """A question goes down the workflow's path: sorted, searched and answered"""
    model.says(routed("question", "ssa"))
    model.says("Apply online [p1].")
    _, router = router_for(model, "ssa")
    assert router.reply("How do I replace my card?") == "Apply online [p1]."
    assert with_tools(model) == [False, False]


@pytest.mark.id("tst_0t55dg")
def test_a_case(model):
    """A case for a service goes down the workflow's path, and waits for the caller's yes"""
    model.says(routed("case", "dmv"))
    desk, router = router_for(model, "dmv")
    router.reply("My new license hasn't come.")
    assert desk.writes == []
    router.reply("Yes, please open the ticket.")
    assert [write["tool"] for write in desk.writes] == ["open_ticket"]
    assert len(model.requests) == 1


@pytest.mark.id("tst_3mnc4q")
def test_a_callback(model):
    """A callback for a service with one open ticket goes down the workflow's path"""
    model.says(routed("callback", "va", "2026-11-03", "14:00"))
    desk, router = router_for(model, None)
    assert "14:00" in router.reply("Can someone call me Tuesday at 14:00 about my GI Bill?")
    router.reply("Yes, please book it.")
    assert [(write["ticket"], write["time"]) for write in desk.writes] == [("T-1901", "14:00")]


@pytest.mark.id("tst_1t1o8k")
def test_a_vague_callback(model):
    """A callback the workflow can't place goes to the agent, which keeps the conversation"""
    model.says(routed("callback", "none", "2026-11-03", "none", "morning"))
    model.says("Which ticket is it about: T-2101 or T-1901?")
    model.says("I'll book T-2101 on Tuesday at 10:00. Shall I?")
    _, router = router_for(model, None)
    assert router.reply("Can someone call me Tuesday morning?").startswith("Which ticket")
    router.reply("The card one.")
    assert with_tools(model) == [False, True, True]
