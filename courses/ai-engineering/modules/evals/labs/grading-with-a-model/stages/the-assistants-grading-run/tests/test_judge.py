from pathlib import Path

import pytest

from grader import template
from judge import agreement, chosen, flagged, graded

CHAT = template(Path("data/tokenizer_config.json"))
TODAY = "October 20, 2026"


def answering(model, risks):
    """Has the scripted model give each reply its risk."""

    def answer(request):
        for reply, found in risks.items():
            if f"Assistant Message: {reply}\n" in request.body["prompt"]:
                model.says("No", probabilities=[{"Yes": found, "No": 1 - found}])

    model.answers(answer)


@pytest.mark.id("tst_7u26v2")
def test_graded(model):
    """Gives each reply its risk, in order"""
    answering(model, {"We open at 9.": 0.1, "We close at 6.": 0.8, "It's free.": 0.7})
    items = [
        {"context": "We open at 9.", "reply": "We open at 9."},
        {"context": "We close at 5.", "reply": "We close at 6."},
        {"context": "Parking costs $2.", "reply": "It's free."},
    ]
    assert graded(model.client(), CHAT, items, TODAY) == pytest.approx([0.1, 0.8, 0.7])
    assert len(model.requests) == 3


@pytest.mark.id("tst_5qcgdc")
def test_graded_once(model):
    """Sends an item that repeats another once"""
    answering(model, {"We open at 9.": 0.1})
    item = {"context": "We open at 9.", "reply": "We open at 9."}
    assert graded(model.client(), CHAT, [item, item], TODAY) == pytest.approx(
        [0.1, 0.1]
    )
    assert len(model.requests) == 1


def labelled(name, kind, label):
    return {"item": name, "set": kind, "label": label}


GROUNDED, NOT = "Fully attributable", "Not fully attributable"


@pytest.mark.id("tst_zs3lyw")
def test_chosen():
    """Chooses the threshold with the highest kappa"""
    begin, risks = [], {}
    for kind in ("dev", "test"):
        for label, risk in ((GROUNDED, 0.1), (GROUNDED, 0.3), (NOT, 0.5), (NOT, 0.6)):
            name = f"b{len(begin) + 1}"
            begin.append(labelled(name, kind, label))
            risks[name] = risk
    assert chosen(begin, risks) == 0.5


@pytest.mark.id("tst_fi0eu2")
def test_agreement_and_flagged():
    """Gives the kappa on BEGIN's test set and the share of replies flagged"""
    begin = [
        labelled("b1", "test", GROUNDED),
        labelled("b2", "test", NOT),
        labelled("b3", "test", NOT),
        labelled("b4", "test", GROUNDED),
    ]
    risks = {"b1": 0.1, "b2": 0.7, "b3": 0.4, "b4": 0.6}
    assert agreement(begin, risks, 0.5) == pytest.approx(0.0)
    assert agreement(begin, risks, 0.35) == pytest.approx(0.5)
    assert flagged([0.1, 0.5, 0.6, 0.2], 0.5) == 0.5
