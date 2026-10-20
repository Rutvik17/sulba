import csv

import numpy as np
import pytest

from report import REPEATS, first_passages, read_runs, report, scores


@pytest.fixture(scope="module")
def desk():
    """The passages' first passages, and the test questions' runs, judgments and services."""
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        first = first_passages(
            {row["passage"]: row["text"] for row in csv.DictReader(file)}
        )
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        tests = [row for row in csv.DictReader(file) if row["set"] == "test"]
    judgments = {row["question"]: set() for row in tests}
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["question"] in judgments:
                judgments[row["question"]].add(row["passage"])
    services = {row["question"]: row["domain"] for row in tests}
    return read_runs(set(judgments)), judgments, first, services


def hits(run, judgments, first):
    """Each judged question's hit rate at 5, by text."""
    found = []
    for question, relevant in judgments.items():
        texts = {first[passage] for passage in relevant}
        shown = [first[passage] for passage in run.get(question, [])[:5]]
        found.append(float(not texts.isdisjoint(shown)))
    return np.array(found)


@pytest.mark.id("tst_xig95w")
def test_every_question(desk):
    """Every test question counted, one the search shows nothing for as 0"""
    runs, judgments, first, services = desk
    chosen = {"reranked": runs["reranked"], "confident": runs["confident"]}
    found = report(
        chosen, "reranked", judgments, first, services, np.random.default_rng(0)
    )
    expected = hits(runs["confident"], judgments, first).mean()
    assert found["confident"]["all"]["hit_rate"] == pytest.approx(expected, abs=1e-12)


@pytest.mark.id("tst_3uuz91")
def test_answer_once():
    """nDCG of 1 for an answer shown first, whatever copies of it there are"""
    first = first_passages(
        {"p1": "Apply online.", "p2": "Call us.", "p3": "Apply online."}
    )
    found = scores({"q1": ["p1", "p2"]}, {"q1": {"p1", "p3"}}, first)
    assert found["q1"][1] == pytest.approx(1)


@pytest.mark.id("tst_o381oc")
def test_copies_keep_their_ranks():
    """A repeated text keeps its rank, so the passages after it don't move up"""
    texts = {"p1": "A", "p2": "B", "p3": "A", "p4": "C", "p5": "D", "p6": "E"}
    first = first_passages(texts)
    found = scores({"q1": ["p1", "p3", "p4", "p5", "p6", "p2"]}, {"q1": {"p2"}}, first)
    assert found["q1"][0] == 0


@pytest.mark.id("tst_pmouf7")
def test_paired(desk):
    """The gain's p-value from each question's two hit rates, swapped as the draws say"""
    runs, judgments, first, services = desk
    chosen = {"fused-once": runs["fused-once"], "reranked": runs["reranked"]}
    found = report(
        chosen, "fused-once", judgments, first, services, np.random.default_rng(5)
    )
    a = hits(runs["reranked"], judgments, first)
    b = hits(runs["fused-once"], judgments, first)
    signs = 1 - 2 * np.random.default_rng(5).integers(0, 2, size=(REPEATS, len(a)))
    count = np.count_nonzero(np.abs(signs @ (a - b)) >= abs((a - b).sum()))
    assert found["reranked"]["all"]["p"] == pytest.approx((1 + count) / (1 + REPEATS))
