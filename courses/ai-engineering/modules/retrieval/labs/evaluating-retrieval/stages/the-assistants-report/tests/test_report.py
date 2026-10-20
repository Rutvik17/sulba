import math

import numpy as np
import pytest

from report import first_passages, report, scores

TEXTS = {"p1": "Apply online.", "p2": "Renew by mail.", "p3": "Call us."}
FIRST = {"p1": "p1", "p2": "p2", "p3": "p3"}


@pytest.mark.id("tst_cynts3")
def test_first_passages():
    """Each passage's text as the first passage that holds it"""
    assert first_passages({"p1": "A", "p2": "B", "p3": "A"}) == {
        "p1": "p1",
        "p2": "p2",
        "p3": "p1",
    }


@pytest.mark.id("tst_xg6zjz")
def test_scores():
    """A question's hit rate and nDCG"""
    found = scores({"q1": ["p2", "p1"]}, {"q1": {"p1"}}, FIRST)
    assert found["q1"][0] == 1
    assert found["q1"][1] == pytest.approx(1 / math.log2(3))


@pytest.mark.id("tst_5fsu2e")
def test_report():
    """Every search, over every question and in each service"""
    runs = {"now": {"q1": ["p1"], "q2": ["p3"]}, "new": {"q1": ["p2"], "q2": ["p2"]}}
    judgments = {"q1": {"p1"}, "q2": {"p2"}}
    services = {"q1": "ssa", "q2": "va"}
    found = report(runs, "now", judgments, FIRST, services, np.random.default_rng(0))
    assert set(found) == {"now", "new"}
    assert set(found["now"]) == {"all", "ssa", "va"}
    assert found["now"]["all"]["hit_rate"] == 0.5
    assert found["new"]["va"]["hit_rate"] == 1


@pytest.mark.id("tst_stfv2s")
def test_same_search():
    """A search against itself gains nothing, with a p-value of 1"""
    runs = {"now": {"q1": ["p1"], "q2": ["p3"]}, "again": {"q1": ["p1"], "q2": ["p3"]}}
    judgments = {"q1": {"p1"}, "q2": {"p2"}}
    services = {"q1": "ssa", "q2": "va"}
    found = report(runs, "now", judgments, FIRST, services, np.random.default_rng(0))
    assert found["again"]["all"]["gain"] == 0
    assert found["again"]["all"]["p"] == 1
