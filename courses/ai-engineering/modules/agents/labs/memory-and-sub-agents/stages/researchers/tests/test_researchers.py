import json

import pytest

from memory import MODEL
from researchers import RESEARCHER, SEARCH, Researchers

SERVICES = {"ssa": "Social Security", "va": "veterans' benefits"}
PASSAGES = (
    "2 passages.\n\n[p17] Replace a card\nApply online.\n\n[p18] Fees\nIt's free."
)


def team(model, searched, **options):
    def search(query, service):
        searched.append((query, service))
        return PASSAGES

    return Researchers(model.client(), search, SERVICES, **options)


@pytest.mark.id("tst_q4b37i")
def test_a_question(model):
    """A question goes to its service's researcher in a conversation of its own: the
    researcher's prompt, the question and search_pages, whose calls search that service"""
    model.says(tool_calls=[("search_pages", {"query": "replace a card"})])
    model.says("Apply online, for free [p17][p18].")
    searched = []
    researchers = team(model, searched)
    answer = researchers.research("ssa", "How do I replace my card?")
    assert answer == "Apply online, for free [p17][p18]."
    assert searched == [("replace a card", "ssa")]
    first, second = model.requests
    assert first.body["model"] == MODEL
    assert first.body["messages"] == [
        {"role": "system", "content": RESEARCHER.format(name="Social Security")},
        {"role": "user", "content": "How do I replace my card?"},
    ]
    assert first.body["tools"] == [SEARCH]
    assert second.body["messages"][-1]["content"] == PASSAGES


@pytest.mark.id("tst_r75yo4")
def test_the_last_round(model):
    """The researcher's last request goes without tools, so that the model answers from what
    it found"""
    model.says(tool_calls=[("search_pages", {"query": "card"})])
    model.says(tool_calls=[("search_pages", {"query": "card fees"})])
    model.says("It's free [p18].")
    researchers = team(model, [], rounds=3)
    assert researchers.research("ssa", "What does a card cost?") == "It's free [p18]."
    assert ["tools" in request.body for request in model.requests] == [
        True,
        True,
        False,
    ]


@pytest.mark.id("tst_ukhc4n")
def test_each_question_afresh(model):
    """Each question starts a conversation of its own, with none of the researcher's earlier
    searches"""
    model.says("Apply online [p17].")
    model.says("It's free [p18].")
    researchers = team(model, [])
    researchers.research("ssa", "How do I replace my card?")
    researchers.research("ssa", "What does it cost?")
    assert [m["role"] for m in model.requests[1].body["messages"]] == ["system", "user"]


@pytest.mark.id("tst_l5v3t8")
def test_the_lead_calls(model):
    """research, called by the lead with its arguments as JSON text, runs the service's
    researcher, and a call it can't run gives an error that says how to call it"""
    model.says("Claims take about 4 months [p40].")
    researchers = team(model, [])
    call = json.dumps({"service": "va", "question": "How long does a claim take?"})
    assert researchers.call("research", call) == "Claims take about 4 months [p40]."
    assert (
        RESEARCHER.format(name="veterans' benefits")
        in (model.requests[0].body["messages"][0]["content"])
    )
    wrong = researchers.call(
        "research", json.dumps({"service": "dmv", "question": "?"})
    )
    assert wrong.startswith("Error:") and "ssa" in wrong and "va" in wrong
    missing = researchers.call("research", json.dumps({"service": "va"}))
    assert missing.startswith("Error:") and "question" in missing
    assert len(model.requests) == 1


@pytest.mark.id("tst_13mwot")
def test_the_tool(model):
    """research's spec names each service the researchers have, and needs a service and a
    question"""
    spec = team(model, []).tool()
    assert spec["type"] == "function" and spec["function"]["name"] == "research"
    parameters = spec["function"]["parameters"]
    assert parameters["properties"]["service"]["enum"] == ["ssa", "va"]
    assert sorted(parameters["required"]) == ["question", "service"]
